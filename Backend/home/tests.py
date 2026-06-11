from datetime import datetime
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from accounts.models import UserProfile
from codes.models import CodeEntry
from prizes.models import Prize, UserPrize
from .models import SurveyQuestion, SurveyOption, SurveyAnswer, Raffle
from .raffledraw import run_draw


class RaffleDrawTests(APITestCase):
    def test_draw_picks_registered_code_and_awards_prize(self):
        u = UserProfile.objects.create(telegram_id=42, name='Амир')
        CodeEntry.objects.create(user=u, code_text='PEPSI-WIN1', status='accepted', reward=50)
        CodeEntry.objects.create(user=u, code_text='PEPSI-LOSE1', status='lose', reward=0)
        Prize.objects.create(title='Главный приз', description='...', is_main=True)
        raffle = Raffle.objects.create(
            title='Тест', draw_at=timezone.make_aware(datetime(2026, 6, 15, 18, 0)))

        entry = run_draw(raffle)
        raffle.refresh_from_db()
        self.assertIsNotNone(entry)
        self.assertEqual(raffle.winner_id, u.id)
        self.assertIn(raffle.winning_code, ['PEPSI-WIN1', 'PEPSI-LOSE1'])
        self.assertTrue(raffle.is_done)
        self.assertEqual(UserPrize.objects.filter(user=u, status='won').count(), 1)
        # повторный розыгрыш не перепроводится
        self.assertIsNone(run_draw(raffle))

    def test_raffles_list_endpoint(self):
        Raffle.objects.create(title='Р1', draw_at=timezone.make_aware(datetime(2026, 6, 15, 18, 0)))
        r = APIClient().get('/api/home/raffles/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data[0]['is_done'], False)


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
