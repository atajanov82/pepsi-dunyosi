"""Проведение розыгрыша.

Механика:
- Пул билетов = коды, успешно введённые ПОСЛЕ предыдущего розыгрыша и до даты текущего
  (статусы accepted/lose). Уже выигравшие коды исключаются.
- Для каждого кода бросается «рулетка»: с вероятностью win_chance% он выигрывает
  конкретный приз. Сумма шансов призов (напр. 2%+12%+19%=33%) — общий шанс выиграть.
- Победитель получает приз (UserPrize 'won' -> вкладка «Выигранные») и запись RaffleWin.
"""
import secrets
from django.utils import timezone
from codes.models import CodeEntry
from prizes.models import Prize, UserPrize
from .models import Raffle, RaffleWin


def _ticket_pool(raffle):
    """Коды-билеты для этого розыгрыша (новые с прошлого розыгрыша, без уже выигравших)."""
    prev = (Raffle.objects.filter(draw_at__lt=raffle.draw_at)
            .order_by('-draw_at').first())
    qs = CodeEntry.objects.filter(status__in=['accepted', 'lose'],
                                  created_at__lte=raffle.draw_at)
    if prev:
        qs = qs.filter(created_at__gt=prev.draw_at)
    won = set(RaffleWin.objects.values_list('code_text', flat=True))
    # по одному билету на уникальный код
    seen, pool = set(), []
    for e in qs.order_by('created_at'):
        if e.code_text in won or e.code_text in seen:
            continue
        seen.add(e.code_text)
        pool.append(e)
    return pool


def run_draw(raffle):
    """Проводит розыгрыш. Возвращает список RaffleWin (победителей)."""
    if raffle.is_done:
        return []
    # призы, участвующие в розыгрыше, по возрастанию шанса (редкие — первыми)
    prizes = list(Prize.objects.filter(win_chance__gt=0).order_by('win_chance'))
    rng = secrets.SystemRandom()
    wins = []
    for entry in _ticket_pool(raffle):
        roll = rng.uniform(0, 100)
        cum = 0.0
        for p in prizes:
            cum += p.win_chance
            if roll < cum:
                win = RaffleWin.objects.create(raffle=raffle, user=entry.user,
                                               prize=p, code_text=entry.code_text)
                UserPrize.objects.get_or_create(user=entry.user, prize=p,
                                                defaults={'status': 'won'})
                wins.append(win)
                break
    raffle.drawn_at = timezone.now()
    raffle.save(update_fields=['drawn_at'])
    return wins
