from rest_framework.test import APITestCase
from accounts.models import UserProfile
from .models import Product, Purchase


class BuyTests(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(telegram_id=1, name='U', balance=100)
        self.cheap = Product.objects.create(name='Pepsi', price=80, stock=2)
        self.dear = Product.objects.create(name='Рюкзак', price=1200, stock=5)
        self.empty = Product.objects.create(name='Нет', price=10, stock=0)

    def buy(self, pid):
        return self.client.post('/api/shop/buy/',
                                {'telegram_id': 1, 'product_id': pid})

    def test_buy_success_debits_balance_and_stock(self):
        r = self.buy(self.cheap.id)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['balance'], 20)
        self.assertEqual(r.data['purchase']['status'], 'assembling')  # статус по умолчанию
        self.user.refresh_from_db(); self.cheap.refresh_from_db()
        self.assertEqual(self.user.balance, 20)
        self.assertEqual(self.cheap.stock, 1)
        self.assertEqual(Purchase.objects.count(), 1)

    def test_my_orders_include_status(self):
        self.buy(self.cheap.id)
        r = self.client.get('/api/shop/my/', {'telegram_id': 1})
        self.assertEqual(r.data[0]['status'], 'assembling')
        self.assertEqual(r.data[0]['status_display'], 'Собирается')

    def test_insufficient_balance(self):
        r = self.buy(self.dear.id)
        self.assertEqual(r.status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, 100)

    def test_out_of_stock(self):
        r = self.buy(self.empty.id)
        self.assertEqual(r.status_code, 400)

    def test_purchases_count_in_prize_stats(self):
        self.buy(self.cheap.id)
        r = self.client.get('/api/prizes/stats/', {'telegram_id': 1})
        self.assertEqual(r.data['purchases'], 1)
