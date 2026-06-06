"""Проверка подписи Telegram WebApp initData.

Документация: данные initData подписываются ботом. Алгоритм проверки:
  secret_key = HMAC_SHA256(key="WebAppData", msg=bot_token)
  hash       = HMAC_SHA256(key=secret_key, msg=data_check_string)
где data_check_string — пары key=value (кроме hash), отсортированные по ключу
и склеенные через '\n'. Подробнее: https://core.telegram.org/bots/webapps
"""
import hashlib
import hmac
import json
from urllib.parse import parse_qsl


def parse_init_data(init_data: str, bot_token: str):
    """Проверяет подпись initData. Возвращает dict пользователя (id, first_name, ...)
    при успехе или None при неверной подписи / отсутствии данных."""
    if not init_data or not bot_token:
        return None
    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None
    received_hash = parsed.pop('hash', None)
    if not received_hash:
        return None

    data_check_string = '\n'.join(f'{k}={parsed[k]}' for k in sorted(parsed))
    secret_key = hmac.new(b'WebAppData', bot_token.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc_hash, received_hash):
        return None

    try:
        return json.loads(parsed.get('user', '{}'))
    except json.JSONDecodeError:
        return None
