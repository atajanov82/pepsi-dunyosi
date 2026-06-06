from django.contrib import admin
from .models import Prize, UserPrize

@admin.register(Prize)
class PrizeAdmin(admin.ModelAdmin):
    list_display = ('title', 'prize_type', 'is_main', 'valid_until')

@admin.register(UserPrize)
class UserPrizeAdmin(admin.ModelAdmin):
    list_display = ('user', 'prize', 'status', 'created_at')
