"""Генерация уникальных промокодов Pepsi.

Коды гарантированно не повторяются (uniqueness на уровне БД + проверка при генерации),
активируются один раз (см. SubmitCodeView: redeemed_by). Алфавит без похожих символов
(нет 0/O/1/I), чтобы их было сложно перепутать при наборе с крышки.
"""
import secrets
from .models import PromoCode

ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # без 0 O 1 I


def _random_code(prefix, length):
    body = ''.join(secrets.choice(ALPHABET) for _ in range(length))
    return f'{prefix}{body}'


def generate_unique_codes(count, reward=50, big_reward=100, big_chance=0.15,
                          prefix='PEPSI-', length=6):
    """Создаёт count уникальных кодов. ВСЕ коды выигрышные: обычно reward (50₽),
    иногда (с вероятностью big_chance, чуть меньше) — big_reward (100₽).
    Возвращает список (код, награда)."""
    existing = set(PromoCode.objects.values_list('code', flat=True))
    fresh = set()
    attempts = 0
    max_attempts = count * 50 + 1000
    while len(fresh) < count and attempts < max_attempts:
        attempts += 1
        code = _random_code(prefix, length)
        if code not in existing and code not in fresh:
            fresh.add(code)

    rng = secrets.SystemRandom()
    rows = [PromoCode(code=c, reward=(big_reward if rng.random() < big_chance else reward))
            for c in fresh]
    PromoCode.objects.bulk_create(rows)
    return sorted((r.code, r.reward) for r in rows)
