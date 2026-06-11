from datetime import datetime
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

    def test_win_chance_100_all_codes_win(self):
        u = UserProfile.objects.create(telegram_id=42, name='Амир')
        for i in range(3):
            self._code(u, f'C{i}')
        Prize.objects.create(title='Комбо', description='...', win_chance=100)
        raffle = Raffle.objects.create(
            title='Тест', draw_at=timezone.make_aware(datetime(2026, 6, 15, 18, 0)))
        wins = run_draw(raffle)
        raffle.refresh_from_db()
        self.assertEqual(len(wins), 3)               # все 3 кода выиграли (шанс 100%)
        self.assertTrue(raffle.is_done)
        self.assertEqual(raffle.wins.count(), 3)
        self.assertEqual(UserPrize.objects.filter(user=u, status='won').count(), 1)
        self.assertEqual(run_draw(raffle), [])       # повторно не проводится

    def test_zero_chance_no_winners(self):
        u = UserProfile.objects.create(telegram_id=43, name='X')
        self._code(u, 'Z1')
        Prize.objects.create(title='Приз', description='...', win_chance=0)
        raffle = Raffle.objects.create(
            title='Т', draw_at=timezone.make_aware(datetime(2026, 6, 15, 18, 0)))
        self.assertEqual(len(run_draw(raffle)), 0)

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
