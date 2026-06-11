from django.conf import settings
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from accounts.models import UserProfile
from accounts.utils import get_user
from .models import Banner, Raffle, SurveyQuestion, SurveyOption, SurveyAnswer
from .serializers import (BannerSerializer, RaffleSerializer,
                          SurveyQuestionSerializer, SubmitSurveySerializer)


class BannerListView(ListAPIView):
    """GET /api/home/banners/ — слайды карусели."""
    queryset = Banner.objects.filter(is_active=True)
    serializer_class = BannerSerializer


class ActiveRaffleView(APIView):
    """GET /api/home/raffle/ — ближайший непроведённый розыгрыш (для таймера)."""
    def get(self, request):
        from django.utils import timezone
        pending = Raffle.objects.filter(is_active=True, winner__isnull=True).order_by('draw_at')
        raffle = (pending.filter(draw_at__gte=timezone.now()).first()
                  or pending.first()
                  or Raffle.objects.order_by('-draw_at').first())
        if not raffle:
            return Response({'detail': 'Нет активного розыгрыша'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(RaffleSerializer(raffle).data)


class RaffleListView(APIView):
    """GET /api/home/raffles/ — все розыгрыши с результатами (Записи розыгрышей)."""
    def get(self, request):
        raffles = Raffle.objects.all().order_by('draw_at')
        return Response(RaffleSerializer(raffles, many=True).data)


class SurveyView(APIView):
    """GET /api/home/survey/ — вопросы опроса."""
    def get(self, request):
        questions = SurveyQuestion.objects.prefetch_related('options').all()
        return Response(SurveyQuestionSerializer(questions, many=True).data)


class SubmitSurveyView(APIView):
    """POST /api/home/survey/submit/ — пройти опрос, получить 250 ₽ (один раз).
    Ответы сохраняются; начисление и установка флага — атомарно."""
    def post(self, request):
        profile = get_user(request)
        s = SubmitSurveySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        answers = s.validated_data['answers']

        # Карта option_id -> question_id для валидации соответствия варианта вопросу
        opt_ids = [a['option'] for a in answers]
        options = {o.id: o.question_id for o in
                   SurveyOption.objects.filter(id__in=opt_ids)}
        for a in answers:
            if options.get(a['option']) != a['question']:
                return Response({'detail': 'Вариант не соответствует вопросу'},
                                status=status.HTTP_400_BAD_REQUEST)

        # Требуем ответ на каждый вопрос опроса
        required = set(SurveyQuestion.objects.values_list('id', flat=True))
        answered = {a['question'] for a in answers}
        if required and required - answered:
            return Response({'detail': 'Нужно ответить на все вопросы'},
                            status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            profile = UserProfile.objects.select_for_update().get(pk=profile.pk)
            if profile.survey_completed:
                return Response({'detail': 'Опрос уже пройден'},
                                status=status.HTTP_400_BAD_REQUEST)
            SurveyAnswer.objects.bulk_create([
                SurveyAnswer(user=profile, question_id=a['question'], option_id=a['option'])
                for a in answers
            ])
            profile.survey_completed = True
            profile.balance += settings.SURVEY_REWARD
            profile.save(update_fields=['survey_completed', 'balance'])

        return Response({'reward': settings.SURVEY_REWARD, 'balance': profile.balance})
