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


def generate_unique_codes(count, reward=50, prefix='PEPSI-', length=6, win_ratio=0.2):
    """Создаёт count уникальных кодов. Примерно win_ratio (по умолчанию 20%) —
    выигрышные (с наградой reward), остальные — проигрышные (reward=0), но тоже
    одноразовые. Победители выбираются случайно. Возвращает (всего, выигрышных)."""
    existing = set(PromoCode.objects.values_list('code', flat=True))
    fresh = set()
    attempts = 0
    max_attempts = count * 50 + 1000
    while len(fresh) < count and attempts < max_attempts:
        attempts += 1
        code = _random_code(prefix, length)
        if code not in existing and code not in fresh:
            fresh.add(code)

    fresh = list(fresh)
    rng = secrets.SystemRandom()
    win_count = round(len(fresh) * win_ratio)
    winners = set(rng.sample(fresh, win_count)) if win_count else set()
    rows = [PromoCode(code=c, reward=(reward if c in winners else 0)) for c in fresh]
    PromoCode.objects.bulk_create(rows)
    # список (код, награда): награда 0 — проигрышный код
    return sorted((r.code, r.reward) for r in rows)
