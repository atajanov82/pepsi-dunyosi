import hashlib
import hmac
import json
from datetime import date
from urllib.parse import urlencode
from django.test import override_settings
from rest_framework.test import APITestCase
from .models import UserProfile


def make_init_data(token, user):
    """Собирает корректно подписанный Telegram initData для тестов."""
    fields = {'auth_date': '1', 'query_id': 'AAA',
              'user': json.dumps(user, separators=(',', ':'))}
    dcs = '\n'.join(f'{k}={fields[k]}' for k in sorted(fields))
    secret = hmac.new(b'WebAppData', token.encode(), hashlib.sha256).digest()
    fields['hash'] = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


@override_settings(TELEGRAM_BOT_TOKEN='test-token', TELEGRAM_ALLOW_INSECURE=False)
class TelegramAuthTests(APITestCase):
    def test_valid_initdata_authenticates(self):
        UserProfile.objects.create(telegram_id=555, name='TG')
        init = make_init_data('test-token', {'id': 555})
        r = self.client.get('/api/accounts/profile/', HTTP_X_TELEGRAM_INIT_DATA=init)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['telegram_id'], 555)

    def test_invalid_signature_rejected(self):
        UserProfile.objects.create(telegram_id=556, name='TG')
        bad = make_init_data('wrong-token', {'id': 556})
        r = self.client.get('/api/accounts/profile/', HTTP_X_TELEGRAM_INIT_DATA=bad)
        self.assertEqual(r.status_code, 403)  # DRF: NotAuthenticated без аутентификатора -> 403

    def test_insecure_disabled_blocks_raw_telegram_id(self):
        UserProfile.objects.create(telegram_id=557, name='TG')
        r = self.client.get('/api/accounts/profile/', {'telegram_id': 557})
        self.assertEqual(r.status_code, 403)  # insecure off -> без подписи доступа нет


class RegisterTests(APITestCase):
    def test_register_creates_profile_once(self):
        r = self.client.post('/api/accounts/register/',
                             {'telegram_id': 1, 'name': 'Иван', 'phone': '+998901234567'})
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.data['created'])
        # повторная регистрация не создаёт дубликат
        r2 = self.client.post('/api/accounts/register/',
                              {'telegram_id': 1, 'name': 'Иван', 'phone': '+998901234567'})
        self.assertEqual(r2.status_code, 200)
        self.assertFalse(r2.data['created'])
        self.assertEqual(UserProfile.objects.count(), 1)

    def test_invalid_phone_rejected(self):
        r = self.client.post('/api/accounts/register/',
                             {'telegram_id': 2, 'name': 'X', 'phone': 'abc'})
        self.assertEqual(r.status_code, 400)

    def test_referral_rewards_inviter(self):
        self.client.post('/api/accounts/register/',
                         {'telegram_id': 10, 'name': 'Пригласивший', 'phone': '+998900000000'})
        self.client.post('/api/accounts/register/',
                         {'telegram_id': 11, 'name': 'Друг', 'phone': '+998900000001', 'ref': 10})
        inviter = UserProfile.objects.get(telegram_id=10)
        friend = UserProfile.objects.get(telegram_id=11)
        self.assertEqual(inviter.balance, 10)          # REFERRAL_REWARD
        self.assertEqual(friend.invited_by_id, inviter.id)
        self.assertEqual(inviter.referrals_count, 1)

    def test_self_referral_ignored(self):
        self.client.post('/api/accounts/register/',
                         {'telegram_id': 20, 'name': 'Сам', 'phone': '+998900000002', 'ref': 20})
        self.assertEqual(UserProfile.objects.get(telegram_id=20).balance, 0)


class OnboardingTests(APITestCase):
    def _user(self, tg=1):
        self.client.post('/api/accounts/register/',
                         {'telegram_id': tg, 'name': 'U', 'phone': '+998900000000'})

    def test_age_below_min_rejected(self):
        self._user()
        too_young = date.today().year - 5
        r = self.client.post('/api/accounts/birth-year/',
                             {'telegram_id': 1, 'birth_year': too_young})
        self.assertEqual(r.status_code, 403)

    def test_valid_age_accepted(self):
        self._user()
        ok_year = date.today().year - 20
        r = self.client.post('/api/accounts/birth-year/',
                             {'telegram_id': 1, 'birth_year': ok_year})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['birth_year'], ok_year)

    def test_future_birth_year_rejected(self):
        self._user()
        r = self.client.post('/api/accounts/birth-year/',
                             {'telegram_id': 1, 'birth_year': date.today().year + 1})
        self.assertEqual(r.status_code, 400)

    def test_onboarding_status_flow(self):
        # незарегистрированный → next_step register
        r = self.client.get('/api/accounts/onboarding/', {'telegram_id': 999})
        self.assertEqual(r.data['next_step'], 'register')
        self._user()
        r = self.client.get('/api/accounts/onboarding/', {'telegram_id': 1})
        self.assertEqual(r.data['next_step'], 'policy')
        self.client.post('/api/accounts/policy/', {'telegram_id': 1, 'accepted': True})
        r = self.client.get('/api/accounts/onboarding/', {'telegram_id': 1})
        self.assertEqual(r.data['next_step'], 'birth_year')
