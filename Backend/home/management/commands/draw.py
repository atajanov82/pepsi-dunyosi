"""Проведение розыгрышей.
    python manage.py draw            — провести все наступившие, ещё не проведённые
    python manage.py draw --id 3     — провести конкретный розыгрыш
    python manage.py draw --all      — провести все непроведённые (без учёта даты)
"""
from django.utils import timezone
from django.core.management.base import BaseCommand
from home.models import Raffle
from home.raffledraw import run_draw


class Command(BaseCommand):
    help = 'Проводит розыгрыши: случайно выбирает выигрышный код.'

    def add_arguments(self, parser):
        parser.add_argument('--id', type=int, default=None)
        parser.add_argument('--all', action='store_true',
                            help='Провести все непроведённые независимо от даты')

    def handle(self, id, all, **opts):
        if id:
            raffles = Raffle.objects.filter(pk=id)
        elif all:
            raffles = Raffle.objects.filter(winner__isnull=True)
        else:
            raffles = Raffle.objects.filter(winner__isnull=True, draw_at__lte=timezone.now())
        done = 0
        for r in raffles:
            entry = run_draw(r)
            if entry:
                done += 1
                self.stdout.write(f'{r.title}: выигрыш — {entry.code_text} ({entry.user})')
            else:
                self.stdout.write(f'{r.title}: пропущен (уже проведён или нет билетов)')
        self.stdout.write(self.style.SUCCESS(f'Проведено розыгрышей: {done}'))
