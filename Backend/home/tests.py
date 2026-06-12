from datetime import datetime
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from accounts.models import UserProfile
from codes.models import CodeEntry
from prizes.models import Prize, UserPrize
from .models import SurveyQuestion, SurveyOption, SurveyAnswer, Raffle
from .raffledraw import run_draw


class RaffleDrawTests(APITestCase):
    def _code(self, user, text, status='accepted'):
        return CodeEntry.objects.create(user=user, code_text=text, status=status, reward=0)

    def test_one_win_per_user_even_with_many_codes(self):
        # один пользователь с 3 кодами и шансом 100% выигрывает РОВНО один раз
        u = UserProfile.objects.create(telegram_id=42, name='Амир')
        for i in range(3):
            self._code(u, f'C{i}')
        Prize.objects.create(title='Комбо', description='...', win_chance=100)
        raffle = Raffle.objects.create(
            title='Тест', draw_at=timezone.make_aware(datetime(2026, 6, 15, 18, 0)))
        wins = run_draw(raffle)
        raffle.refresh_from_db()
        self.assertEqual(len(wins), 1)               # не 3 — максимум один на человека
        self.assertTrue(raffle.is_done)
        self.assertEqual(raffle.wins.count(), 1)
        self.assertEqual(UserPrize.objects.filter(user=u, status='won').count(), 1)
        self.assertEqual(run_draw(raffle), [])       # повторно не проводится

    @override_settings(RAFFLE_REPEAT_WIN_FACTOR=0)
    def test_prior_winner_excluded_when_factor_zero(self):
        # два пользователя; первый выиграл в r1, во r2 (factor=0) выиграть не может
        u1 = UserProfile.objects.create(telegram_id=51, name='A')
        u2 = UserProfile.objects.create(telegram_id=52, name='B')
        Prize.objects.create(title='Комбо', description='...', win_chance=100)
        r1 = Raffle.objects.create(title='Р1', draw_at=timezone.make_aware(datetime(2026, 6, 15, 18, 0)))
        r2 = Raffle.objects.create(title='Р2', draw_at=timezone.make_aware(datetime(2026, 6, 22, 18, 0)))
        c1 = self._code(u1, 'A1'); CodeEntry.objects.filter(pk=c1.pk).update(
            created_at=timezone.make_aware(datetime(2026, 6, 10, 12, 0)))
        run_draw(r1)
        self.assertEqual(r1.wins.count(), 1)         # u1 выиграл
        # во второй розыгрыш оба вводят новые коды; u1 уже победитель -> factor 0 -> не выигрывает
        for u, t in [(u1, 'A2'), (u2, 'B2')]:
            c = self._code(u, t); CodeEntry.objects.filter(pk=c.pk).update(
                created_at=timezone.make_aware(datetime(2026, 6, 18, 12, 0)))
        run_draw(r2)
        winners2 = set(r2.wins.values_list('user_id', flat=True))
        self.assertIn(u2.id, winners2)
        self.assertNotIn(u1.id, winners2)            # прошлый победитель исключён при factor=0

    def test_zero_chance_no_winners(self):
        u = UserProfile.objects.create(telegram_id=43, name='X')
        self._code(u, 'Z1')
        Prize.objects.create(title='Приз', description='...', win_chance=0)
        raffle = Raffle.objects.create(
            title='Т', draw_at=timezone.make_aware(datetime(2026, 6, 15, 18, 0)))
        self.assertEqual(len(run_draw(raffle)), 0)

    @override_settings(RAFFLE_REPEAT_WIN_FACTOR=1.0)
    def test_incremental_pool_only_new_codes(self):
        u = UserProfile.objects.create(telegram_id=44, name='Y')
        Prize.objects.create(title='Комбо', description='...', win_chance=100)
        r1 = Raffle.objects.create(title='Р1', draw_at=timezone.make_aware(datetime(2026, 6, 15, 18, 0)))
        r2 = Raffle.objects.create(title='Р2', draw_at=timezone.make_aware(datetime(2026, 6, 22, 18, 0)))
        # код «до 15-го»
        old = self._code(u, 'OLD'); CodeEntry.objects.filter(pk=old.pk).update(
            created_at=timezone.make_aware(datetime(2026, 6, 10, 12, 0)))
        run_draw(r1)
        self.assertEqual(r1.wins.count(), 1)
        # новый код «после 15-го» учитывается только во втором розыгрыше
        new = self._code(u, 'NEW'); CodeEntry.objects.filter(pk=new.pk).update(
            created_at=timezone.make_aware(datetime(2026, 6, 18, 12, 0)))
        run_draw(r2)
        self.assertEqual(r2.wins.count(), 1)
        self.assertEqual(r2.wins.first().code_text, 'NEW')

    def test_raffles_list_endpoint(self):
        Raffle.objects.create(title='Р1', draw_at=timezone.make_aware(datetime(2026, 6, 15, 18, 0)))
        r = APIClient().get('/api/home/raffles/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data[0]['is_done'], False)
        self.assertEqual(r.data[0]['winners_count'], 0)


class SurveyTests(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(telegram_id=1, name='U')
        self.q1 = SurveyQuestion.objects.create(text='Q1', order=1)
        self.q1o1 = SurveyOption.objects.create(question=self.q1, text='A')
        self.q1o2 = SurveyOption.objects.create(question=self.q1, text='B')
        self.q2 = SurveyQuestion.objects.create(text='Q2', order=2)
        self.q2o1 = SurveyOption.objects.create(question=self.q2, text='C')

    def submit(self, answers):
        return self.client.post('/api/home/survey/submit/',
                                {'telegram_id': 1, 'answers': answers}, format='json')

    def test_full_survey_rewards_once_and_saves_answers(self):
        r = self.submit([{'question': self.q1.id, 'option': self.q1o1.id},
                         {'question': self.q2.id, 'option': self.q2o1.id}])
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['reward'], 250)
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, 250)
        self.assertTrue(self.user.survey_completed)
        self.assertEqual(SurveyAnswer.objects.filter(user=self.user).count(), 2)
        # повторное прохождение запрещено
        r2 = self.submit([{'question': self.q1.id, 'option': self.q1o1.id},
                          {'question': self.q2.id, 'option': self.q2o1.id}])
        self.assertEqual(r2.status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, 250)

    def test_incomplete_survey_rejected(self):
        r = self.submit([{'question': self.q1.id, 'option': self.q1o1.id}])
        self.assertEqual(r.status_code, 400)
        self.user.refresh_from_db()
        self.assertFalse(self.user.survey_completed)

    def test_option_must_match_question(self):
        r = self.submit([{'question': self.q1.id, 'option': self.q2o1.id},
                         {'question': self.q2.id, 'option': self.q2o1.id}])
        self.assertEqual(r.status_code, 400)
