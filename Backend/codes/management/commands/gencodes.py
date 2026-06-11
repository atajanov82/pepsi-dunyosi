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
        parser.add_argument('--reward', type=int, default=50, help='Награда за код, ₽')
        parser.add_argument('--prefix', default='PEPSI-', help='Префикс кода')
        parser.add_argument('--length', type=int, default=6, help='Длина случайной части')

    def handle(self, count, reward, prefix, length, **opts):
        codes = generate_unique_codes(count, reward=reward, prefix=prefix, length=length)
        for c in codes:
            self.stdout.write(c)
        self.stdout.write(self.style.SUCCESS(
            f'Создано {len(codes)} кодов, награда {reward} руб. за каждый.'))
