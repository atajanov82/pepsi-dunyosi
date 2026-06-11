from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from .models import Product, Purchase


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Управление товарами и учёт остатков."""
    list_display = ('name', 'price', 'stock', 'status_badge', 'sold', 'is_active')
    list_editable = ('price', 'stock', 'is_active')   # править цену/остаток прямо в списке
    list_filter = ('is_active',)
    search_fields = ('name',)
    fields = ('name', 'description', 'image_url', 'price', 'stock', 'is_active')

    def get_queryset(self, request):
        # считаем количество покупок для колонки «Продано» одним запросом
        return super().get_queryset(request).annotate(_sold=Count('purchase'))

    @admin.display(description='Наличие', ordering='stock')
    def status_badge(self, obj):
        if obj.stock == 0:
            color, text = '#dc2626', 'Нет в наличии'
        elif obj.stock <= 5:
            color, text = '#d97706', 'Заканчивается'
        else:
            color, text = '#16a34a', 'В наличии'
        return format_html('<b style="color:{}">{}</b>', color, text)

    @admin.display(description='Продано', ordering='_sold')
    def sold(self, obj):
        return obj._sold


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'price_paid', 'status', 'created_at')
    list_filter = ('status', 'product')
    list_editable = ('status',)   # менять статус доставки прямо из списка
    search_fields = ('user__name', 'user__telegram_id', 'product__name')
    list_select_related = ('user', 'product')
