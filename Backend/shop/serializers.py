from rest_framework import serializers
from .models import Product, Purchase


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'image_url', 'price', 'stock']


class PurchaseSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Purchase
        fields = ['id', 'product', 'price_paid', 'status', 'status_display', 'created_at']


class BuySerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
