from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.models import UserProfile
from accounts.utils import get_user
from .models import PromoCode, CodeEntry
from .serializers import SubmitCodeSerializer, CodeEntrySerializer


class SubmitCodeView(APIView):
    """POST /api/codes/submit/ — отправить код.
    Логика: ищем код в пуле -> неверный / уже использован / принят (+ начисление).
    Активация и начисление выполняются атомарно (блокируем строку кода и профиль)."""
    throttle_scope = 'code_submit'  # защита от перебора промокодов

    def post(self, request):
        profile = get_user(request)
        s = SubmitCodeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        code_text = s.validated_data['code'].strip().upper()

        with transaction.atomic():
            promo = (PromoCode.objects
                     .select_for_update()
                     .filter(code=code_text, is_active=True)
                     .first())

            if promo is None:
                status_, reward = 'invalid', 0
            elif promo.redeemed_by_id is not None:
                status_, reward = 'used', 0
            else:
                status_, reward = 'accepted', promo.reward
                promo.redeemed_by = profile
                promo.redeemed_at = timezone.now()
                promo.save(update_fields=['redeemed_by', 'redeemed_at'])
                # блокируем профиль перед изменением баланса, чтобы избежать гонки
                profile = UserProfile.objects.select_for_update().get(pk=profile.pk)
                profile.balance += reward
                profile.save(update_fields=['balance'])

            entry = CodeEntry.objects.create(user=profile, code_text=code_text,
                                             status=status_, reward=reward)

        return Response({'entry': CodeEntrySerializer(entry).data,
                         'balance': profile.balance})


class CodeHistoryView(APIView):
    """GET /api/codes/history/?telegram_id=... — история + статистика."""
    def get(self, request):
        profile = get_user(request)
        entries = profile.code_entries.all()
        total = (entries.filter(status='accepted')
                 .aggregate(s=Sum('reward'))['s'] or 0)
        return Response({
            'codes_sent': entries.count(),
            'total_rubles': total,
            'entries': CodeEntrySerializer(entries, many=True).data,
        })
