from django.db import transaction
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from accounts.models import UserProfile
from accounts.utils import get_user
from .models import Product, Purchase
from .serializers import ProductSerializer, PurchaseSerializer, BuySerializer


class ProductListView(ListAPIView):
    """GET /api/shop/products/ — каталог магазина."""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer


class BuyView(APIView):
    """POST /api/shop/buy/ — купить товар за рубли (списывает с баланса).
    Списание баланса и уменьшение остатка — атомарно, со взятием строк под блокировку."""
    throttle_scope = 'buy'

    def post(self, request):
        profile = get_user(request)
        s = BuySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        product_id = s.validated_data['product_id']

        with transaction.atomic():
            product = (Product.objects
                       .select_for_update()
                       .filter(id=product_id, is_active=True)
                       .first())
            if product is None:
                return Response({'detail': 'Товар не найден'},
                                status=status.HTTP_404_NOT_FOUND)
            if product.stock <= 0:
                return Response({'detail': 'Товара нет в наличии'},
                                status=status.HTTP_400_BAD_REQUEST)

            profile = UserProfile.objects.select_for_update().get(pk=profile.pk)
            if profile.balance < product.price:
                return Response({'detail': 'Недостаточно рублей'},
                                status=status.HTTP_400_BAD_REQUEST)

            profile.balance -= product.price
            profile.save(update_fields=['balance'])
            product.stock -= 1
            product.save(update_fields=['stock'])
            purchase = Purchase.objects.create(user=profile, product=product,
                                               price_paid=product.price)

        return Response({'purchase': PurchaseSerializer(purchase).data,
                         'balance': profile.balance})


class MyPurchasesView(APIView):
    """GET /api/shop/my/?telegram_id=... — мои покупки."""
    def get(self, request):
        profile = get_user(request)
        return Response(PurchaseSerializer(profile.purchases.all(), many=True).data)
