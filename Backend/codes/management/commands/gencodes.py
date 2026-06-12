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
        parser.add_argument('--reward', type=int, default=50, help='Обычная награда, ₽')
        parser.add_argument('--big-reward', type=int, default=100, help='Крупная награда, ₽')
        parser.add_argument('--big-chance', type=float, default=0.15,
                            help='Доля кодов с крупной наградой (0.15 = 15%%)')
        parser.add_argument('--prefix', default='PEPSI-', help='Префикс кода')
        parser.add_argument('--length', type=int, default=6, help='Длина случайной части')

    def handle(self, count, reward, big_reward, big_chance, prefix, length, **opts):
        rows = generate_unique_codes(count, reward=reward, big_reward=big_reward,
                                     big_chance=big_chance, prefix=prefix, length=length)
        big = sum(1 for _, r in rows if r >= big_reward)
        for code, r in rows:
            self.stdout.write(f'{code}  +{r}')
        self.stdout.write(self.style.SUCCESS(
            f'Создано {len(rows)} кодов: {big} по {big_reward} руб., {len(rows)-big} по {reward} руб.'))
