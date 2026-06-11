from django.contrib import admin, messages
from .models import Banner, Raffle, RaffleWin, SurveyQuestion, SurveyOption, SurveyAnswer
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
    list_display = ('title', 'draw_at', 'is_done', 'winners_count', 'drawn_at')
    list_filter = ('is_active',)
    actions = ['do_draw']

    @admin.display(description='Победителей')
    def winners_count(self, obj):
        return obj.wins.count()

    @admin.action(description='🎰 Провести розыгрыш сейчас (рулетка)')
    def do_draw(self, request, queryset):
        for raffle in queryset:
            if raffle.is_done:
                self.message_user(request, f'{raffle.title}: уже проведён', messages.WARNING)
                continue
            wins = run_draw(raffle)
            self.message_user(
                request, f'{raffle.title}: победителей — {len(wins)}', messages.SUCCESS)


@admin.register(RaffleWin)
class RaffleWinAdmin(admin.ModelAdmin):
    list_display = ('raffle', 'code_text', 'prize', 'user', 'created_at')
    list_filter = ('raffle', 'prize')
    search_fields = ('code_text', 'user__name')
    list_select_related = ('raffle', 'prize', 'user')

admin.site.register(Banner)
