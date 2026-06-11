"""Проведение розыгрыша: рулетка случайно выбирает выигрышный код среди
зарегистрированных (любой успешно введённый код — это билет: статусы accepted/lose).
Победитель получает главный приз (UserPrize 'won')."""
import secrets
from django.utils import timezone
from codes.models import CodeEntry
from prizes.models import Prize, UserPrize
from .models import Raffle


def run_draw(raffle):
    """Проводит один розыгрыш. Возвращает выигравшую CodeEntry или None."""
    if raffle.is_done:
        return None
    # коды, уже выигравшие в других розыгрышах, исключаем — у каждого розыгрыша свой код
    used = set(Raffle.objects.exclude(pk=raffle.pk)
               .exclude(winning_code='').values_list('winning_code', flat=True))
    pool = list(CodeEntry.objects.filter(status__in=['accepted', 'lose'])
                .exclude(code_text__in=used))
    if not pool:
        return None
    entry = secrets.choice(pool)          # рулетка
    raffle.winner = entry.user
    raffle.winning_code = entry.code_text
    raffle.drawn_at = timezone.now()
    raffle.save(update_fields=['winner', 'winning_code', 'drawn_at'])
    # начисляем приз победителю (попадёт во вкладку «Выигранные»)
    prize = Prize.objects.filter(is_main=True).first() or Prize.objects.first()
    if prize:
        UserPrize.objects.get_or_create(user=entry.user, prize=prize,
                                        defaults={'status': 'won'})
    return entry
