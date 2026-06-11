from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from .models import PromoCode, CodeEntry
from .codegen import generate_unique_codes


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'reward', 'is_active', 'redeemed_by', 'redeemed_at')
    list_filter = ('is_active',)
    search_fields = ('code',)
    change_list_template = 'admin/codes/promocode/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom = [path('gencodes/', self.admin_site.admin_view(self.gencodes_view),
                       name='codes_promocode_gencodes')]
        return custom + urls

    def gencodes_view(self, request):
        try:
            n = max(1, min(2000, int(request.GET.get('n', 50))))
        except ValueError:
            n = 50
        codes = generate_unique_codes(n, reward=50)
        self.message_user(request, f'Создано {len(codes)} уникальных кодов по 50 ₽.',
                          messages.SUCCESS)
        return redirect('..')


@admin.register(CodeEntry)
class CodeEntryAdmin(admin.ModelAdmin):
    list_display = ('code_text', 'user', 'status', 'reward', 'created_at')
    list_filter = ('status',)
    search_fields = ('code_text',)
