"""Генератор промокодов. Примеры:
    python manage.py gencodes 100
    python manage.py gencodes 500 --reward 25 --prefix PEPSI- --length 7
Коды печатаются в вывод — можно сохранить и нанести под крышки."""
from django.core.management.base import BaseCommand
from codes.codegen import generate_unique_codes


class Command(BaseCommand):
    help = 'Генерирует уникальные одноразовые промокоды Pepsi.'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, help='Сколько кодов создать')
        parser.add_argument('--reward', type=int, default=50, help='Награда за выигрышный код')
        parser.add_argument('--prefix', default='PEPSI-', help='Префикс кода')
        parser.add_argument('--length', type=int, default=6, help='Длина случайной части')
        parser.add_argument('--win-ratio', type=float, default=0.2,
                            help='Доля выигрышных кодов (0.2 = 20%%)')

    def handle(self, count, reward, prefix, length, win_ratio, **opts):
        rows = generate_unique_codes(count, reward=reward, prefix=prefix,
                                     length=length, win_ratio=win_ratio)
        wins = 0
        for code, r in rows:
            mark = f'ВЫИГРЫШ +{r}' if r > 0 else 'нет'
            if r > 0:
                wins += 1
            self.stdout.write(f'{code}  {mark}')
        self.stdout.write(self.style.SUCCESS(
            f'Создано {len(rows)} кодов: {wins} выигрышных, {len(rows)-wins} проигрышных.'))
