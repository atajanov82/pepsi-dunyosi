from django.contrib import admin
from .models import Product, Purchase

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'is_active')

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'price_paid', 'status', 'created_at')
    list_filter = ('status',)
    list_editable = ('status',)   # менять статус доставки прямо из списка
