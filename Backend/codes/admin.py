from django.contrib import admin
from .models import PromoCode, CodeEntry

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'reward', 'is_active', 'redeemed_by', 'redeemed_at')
    search_fields = ('code',)

@admin.register(CodeEntry)
class CodeEntryAdmin(admin.ModelAdmin):
    list_display = ('code_text', 'user', 'status', 'reward', 'created_at')
