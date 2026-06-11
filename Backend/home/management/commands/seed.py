"""Заполняет БД демо-данными под фронтенд-прототип. Идемпотентно: повторный
запуск не плодит дубликаты. Использование: python manage.py seed"""
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from codes.models import PromoCode
from home.models import Banner, Raffle, SurveyQuestion, SurveyOption
from prizes.models import Prize
from shop.models import Product

# Промокоды совпадают с пулом во фронтенде (VALID_CODES в pepsi.html)
PROMO = {'PEPSI2026': 50, 'PEPSI100': 100, 'COLA50': 25, 'DUNYOSI': 75, 'CHAMPION': 50}

BANNERS = [
    ('ПЕЙ · ВЫИГРЫВАЙ', 'https://placehold.co/600x300/004B93/fff?text=ПЕЙ+ВЫИГРЫВАЙ'),
    ('МИЛЛИОНЫ ПРИЗОВ', 'https://placehold.co/600x300/1e63ff/fff?text=МИЛЛИОНЫ+ПРИЗОВ'),
    ('КАЖДЫЙ ДЕНЬ', 'https://placehold.co/600x300/E32934/fff?text=КАЖДЫЙ+ДЕНЬ'),
]

PRIZES = [
    ('Pepsi Комбо Чемпионов', 'Ваучер на скидку у партнёров сети быстрого питания. Действует 30 дней.', 'combo', False),
    ('Pepsi Сет Чемпионов', 'Набор из 2 бутылок Pepsi 1.5л и подарочного мерча. Доставка бесплатно.', 'set', False),
    ('Главный приз — 100 000 000 сум', 'Денежный сертификат главного приза акции. Розыгрыш в прямом эфире.', 'cash', True),
]

PRODUCTS = [
    ('Pepsi 1.5 л', 80, 100),
    ('Pepsi Max 0.5 л', 40, 100),
    ('Кепка Pepsi', 300, 50),
    ('Футболка Pepsi', 600, 30),
    ('Рюкзак Pepsi', 1200, 10),
]

SURVEY = [
    ('Как часто вы пьёте Pepsi?',
     ['Каждый день', 'Несколько раз в неделю', 'Редко', 'Только по праздникам']),
    ('Какой объём предпочитаете?',
     ['0.5 л', '1 л', '1.5 л', '2 л']),
    ('С чем Pepsi сочетается лучше всего?',
     ['Пицца', 'Бургер', 'Шашлык', 'Попкорн']),
    ('Какой вкус Pepsi вам ближе?',
     ['Classic', 'Pepsi Max', 'Без сахара', 'Wild Cherry']),
    ('Как любите пить Pepsi?',
     ['Холодной со льдом', 'Просто холодной', 'Комнатной температуры', 'Без разницы']),
    ('Где чаще всего пьёте Pepsi?',
     ['Дома', 'В кафе и ресторанах', 'На улице', 'На вечеринках']),
    ('Что выберете в жару?',
     ['Холодную Pepsi', 'Воду', 'Сок', 'Чай со льдом']),
    ('Pepsi или чай к еде?',
     ['Только Pepsi', 'Чаще Pepsi', 'Зависит от блюда', 'Чаще чай']),
    ('Из чего приятнее пить Pepsi?',
     ['Из банки', 'Из бутылки', 'Из стакана со льдом', 'Без разницы']),
    ('Что для вас Pepsi?',
     ['Вкус праздника', 'Заряд бодрости', 'Привычка', 'Лучший напиток к еде']),
]


class Command(BaseCommand):
    help = 'Заполняет БД демо-данными (промокоды, баннеры, призы, товары, опрос, розыгрыш).'

    def handle(self, *args, **options):
        for code, reward in PROMO.items():
            PromoCode.objects.get_or_create(code=code, defaults={'reward': reward})

        for i, (title, url) in enumerate(BANNERS):
            Banner.objects.get_or_create(title=title, defaults={'image_url': url, 'order': i})

        for title, desc, ptype, is_main in PRIZES:
            Prize.objects.get_or_create(
                title=title,
                defaults={'description': desc, 'prize_type': ptype, 'is_main': is_main})

        for name, price, stock in PRODUCTS:
            Product.objects.get_or_create(name=name, defaults={'price': price, 'stock': stock})

        for order, (text, opts) in enumerate(SURVEY):
            q, _ = SurveyQuestion.objects.get_or_create(text=text, defaults={'order': order})
            for opt in opts:
                SurveyOption.objects.get_or_create(question=q, text=opt)

        # 5 дат розыгрышей: 15, 22, 25, 29 июня и финал 1 июля 2026
        raffle_dates = [
            ('Розыгрыш 15 июня',  datetime(2026, 6, 15, 18, 0)),
            ('Розыгрыш 22 июня',  datetime(2026, 6, 22, 18, 0)),
            ('Розыгрыш 25 июня',  datetime(2026, 6, 25, 18, 0)),
            ('Розыгрыш 29 июня',  datetime(2026, 6, 29, 18, 0)),
            ('Финальный розыгрыш — 1 июля', datetime(2026, 7, 1, 18, 0)),
        ]
        for title, dt in raffle_dates:
            Raffle.objects.get_or_create(
                title=title,
                defaults={'draw_at': timezone.make_aware(dt), 'is_active': True})

        self.stdout.write(self.style.SUCCESS('Демо-данные загружены.'))
