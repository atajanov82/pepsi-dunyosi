"""Определение пользователя по запросу. Используется во всех приложениях.

Порядок:
  1) Telegram initData (заголовок X-Telegram-Init-Data или поле init_data) — проверяется подпись.
  2) dev-фолбэк: telegram_id из запроса, если settings.TELEGRAM_ALLOW_INSECURE (для прототипа в браузере).
"""
from django.conf import settings
from rest_framework.exceptions import NotAuthenticated
from .models import UserProfile
from .telegram import parse_init_data


def verified_telegram_id(request):
    """Возвращает telegram_id из проверенного initData, либо None.

    - Токен задан и подпись верна -> возвращаем id.
    - Токен не задан ИЛИ подпись неверна:
        * TELEGRAM_ALLOW_INSECURE=True  -> None (определит dev-фолбэк по telegram_id);
        * TELEGRAM_ALLOW_INSECURE=False -> NotAuthenticated (строгий прод)."""
    init_data = (request.headers.get('X-Telegram-Init-Data')
                 or (request.data.get('init_data') if hasattr(request, 'data') else None))
    if not init_data:
        return None
    if settings.TELEGRAM_BOT_TOKEN:
        tg_user = parse_init_data(init_data, settings.TELEGRAM_BOT_TOKEN,
                                  settings.TELEGRAM_INITDATA_MAX_AGE)
        if tg_user and tg_user.get('id'):
            return tg_user['id']
    if settings.TELEGRAM_ALLOW_INSECURE:
        return None
    raise NotAuthenticated('Неверная подпись Telegram initData')


def resolve_telegram_id(request):
    """telegram_id для регистрации: из initData, иначе (в dev) из тела запроса."""
    tg = verified_telegram_id(request)
    if tg is not None:
        return tg
    if settings.TELEGRAM_ALLOW_INSECURE:
        return request.data.get('telegram_id') or request.query_params.get('telegram_id')
    raise NotAuthenticated('Нужна авторизация Telegram')


def get_user(request):
    """Профиль текущего пользователя (для авторизованных эндпоинтов)."""
    tg = verified_telegram_id(request)
    if tg is None and settings.TELEGRAM_ALLOW_INSECURE:
        tg = request.data.get('telegram_id') or request.query_params.get('telegram_id')
    if not tg:
        raise NotAuthenticated('Нужна авторизация Telegram')
    try:
        tg = int(tg)   # telegram_id всегда числовой; иначе — не валидный запрос
    except (TypeError, ValueError):
        raise NotAuthenticated('Некорректный telegram_id')
    try:
        return UserProfile.objects.get(telegram_id=tg)
    except UserProfile.DoesNotExist:
        raise NotAuthenticated('Пользователь не зарегистрирован')
