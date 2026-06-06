from rest_framework.test import APITestCase
from accounts.models import UserProfile
from .models import SurveyQuestion, SurveyOption, SurveyAnswer


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
