from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from accounts.utils import get_user
from shop.models import Purchase
from shop.serializers import PurchaseSerializer
from .models import Prize, UserPrize
from .serializers import PrizeSerializer, UserPrizeSerializer


class PrizeListView(ListAPIView):
    """GET /api/prizes/ — список всех разыгрываемых призов (вкладка 'Все призы')."""
    queryset = Prize.objects.all()
    serializer_class = PrizeSerializer


class MyPrizesView(APIView):
    """GET /api/prizes/my/?telegram_id=...&tab=won|purchased — мои призы по вкладкам.
    Вкладка 'purchased' берётся из shop.Purchase (единый источник покупок)."""
    def get(self, request):
        profile = get_user(request)
        tab = request.query_params.get('tab')
        if tab == 'purchased':
            purchases = profile.purchases.select_related('product')
            return Response(PurchaseSerializer(purchases, many=True).data)
        qs = profile.user_prizes.select_related('prize')
        if tab == 'won':
            qs = qs.filter(status='won')
        elif tab == 'pending':
            qs = qs.filter(status='pending')
        return Response(UserPrizeSerializer(qs, many=True).data)


class PrizeStatsView(APIView):
    """GET /api/prizes/stats/?telegram_id=... — счётчики Получено / Ожидают / Покупки.
    Покупки считаются из shop.Purchase."""
    def get(self, request):
        profile = get_user(request)
        qs = profile.user_prizes
        return Response({
            'received': qs.filter(status='won').count(),
            'pending':  qs.filter(status='pending').count(),
            'purchases': profile.purchases.count(),
        })
