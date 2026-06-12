from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from accounts.models import UserProfile
from .models import PromoCode


class AdminGenCodesTests(APITestCase):
    def setUp(self):
        User.objects.create_superuser('boss', 'b@e.com', 'pass12345')
        self.client.login(username='boss', password='pass12345')

    def test_changelist_renders(self):
        r = self.client.get('/admin/codes/promocode/')
        self.assertEqual(r.status_code, 200)   # кастомный шаблон с кнопками рендерится

    def test_gencodes_get_not_allowed(self):
        r = self.client.get('/admin/codes/promocode/gencodes/')
        self.assertEqual(r.status_code, 405)   # GET запрещён (анти-CSRF)

    def test_gencodes_post_creates(self):
        r = self.client.post('/admin/codes/promocode/gencodes/', {'n': 5})
        self.assertIn(r.status_code, (200, 302))
        self.assertGreaterEqual(PromoCode.objects.count(), 5)


class SubmitCodeTests(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(telegram_id=1, name='U')
        PromoCode.objects.create(code='PEPSI2026', reward=50)
        PromoCode.objects.create(code='LOSE0001', reward=0)   # проигрышный код

    def submit(self, code):
        return self.client.post('/api/codes/submit/',
                                {'telegram_id': 1, 'code': code})

    def test_valid_code_accepted_and_rewarded(self):
        r = self.submit('pepsi2026')          # регистр и пробелы нормализуются
        self.assertEqual(r.data['entry']['status'], 'accepted')
        self.assertEqual(r.data['balance'], 50)
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, 50)

    def test_losing_code_accepted_no_reward_but_consumed(self):
        r = self.submit('LOSE0001')
        self.assertEqual(r.data['entry']['status'], 'lose')
        self.assertEqual(r.data['balance'], 0)
        # код одноразовый: повторно — «уже использован»
        r2 = self.submit('LOSE0001')
        self.assertEqual(r2.data['entry']['status'], 'used')

    def test_invalid_code(self):
        r = self.submit('NETU')
        self.assertEqual(r.data['entry']['status'], 'invalid')
        self.assertEqual(r.data['balance'], 0)

    def test_code_used_once(self):
        self.submit('PEPSI2026')
        r = self.submit('PEPSI2026')          # тем же пользователем повторно
        self.assertEqual(r.data['entry']['status'], 'used')
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, 50)   # без повторного начисления

    def test_history_totals(self):
        self.submit('PEPSI2026')
        self.submit('NETU')
        r = self.client.get('/api/codes/history/', {'telegram_id': 1})
        self.assertEqual(r.data['codes_sent'], 2)
        self.assertEqual(r.data['total_rubles'], 50)
