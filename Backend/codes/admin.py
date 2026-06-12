from django.contrib import admin, messages
from django.http import HttpResponseNotAllowed
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
        # только POST (изменяющее действие) — защита от CSRF через GET-ссылку
        if request.method != 'POST':
            return HttpResponseNotAllowed(['POST'])
        try:
            n = max(1, min(2000, int(request.POST.get('n') or request.GET.get('n', 50))))
        except (TypeError, ValueError):
            n = 50
        rows = generate_unique_codes(n)   # все выигрышные: 50₽, иногда 100₽
        big = sum(1 for _, r in rows if r >= 100)
        self.message_user(
            request,
            f'Создано {len(rows)} кодов: {big} по 100 ₽, {len(rows)-big} по 50 ₽.',
            messages.SUCCESS)
        return redirect('..')


@admin.register(CodeEntry)
class CodeEntryAdmin(admin.ModelAdmin):
    list_display = ('code_text', 'user', 'status', 'reward', 'created_at')
    list_filter = ('status',)
    search_fields = ('code_text',)
