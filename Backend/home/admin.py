from django.contrib import admin, messages
from .models import Banner, Raffle, SurveyQuestion, SurveyOption, SurveyAnswer
from .raffledraw import run_draw

class OptionInline(admin.TabularInline):
    model = SurveyOption; extra = 2

@admin.register(SurveyQuestion)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [OptionInline]

@admin.register(SurveyAnswer)
class SurveyAnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'option', 'created_at')
    list_select_related = ('user', 'question', 'option')


@admin.register(Raffle)
class RaffleAdmin(admin.ModelAdmin):
    list_display = ('title', 'draw_at', 'is_done', 'winning_code', 'winner', 'drawn_at')
    list_filter = ('is_active',)
    actions = ['do_draw']

    @admin.action(description='🎰 Провести розыгрыш сейчас (рулетка)')
    def do_draw(self, request, queryset):
        done = 0
        for raffle in queryset:
            entry = run_draw(raffle)
            if entry:
                done += 1
                self.message_user(
                    request, f'{raffle.title}: выиграл код {entry.code_text} ({entry.user})',
                    messages.SUCCESS)
            else:
                self.message_user(
                    request, f'{raffle.title}: пропущен (уже проведён или нет билетов)',
                    messages.WARNING)
        if done:
            self.message_user(request, f'Проведено розыгрышей: {done}', messages.SUCCESS)

admin.site.register(Banner)
