from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'name', 'balance', 'policy_accepted', 'created_at')
    search_fields = ('telegram_id', 'name', 'phone')
