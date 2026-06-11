from django.contrib import admin
from .models import Prize, UserPrize

@admin.register(Prize)
class PrizeAdmin(admin.ModelAdmin):
    list_display = ('title', 'prize_type', 'win_chance', 'is_main', 'valid_until')
    list_editable = ('win_chance',)   # настраивать шанс выигрыша прямо в списке

@admin.register(UserPrize)
class UserPrizeAdmin(admin.ModelAdmin):
    list_display = ('user', 'prize', 'status', 'created_at')
