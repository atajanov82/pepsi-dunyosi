from django.contrib import admin
from .models import Banner, Raffle, SurveyQuestion, SurveyOption, SurveyAnswer

class OptionInline(admin.TabularInline):
    model = SurveyOption; extra = 2

@admin.register(SurveyQuestion)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [OptionInline]

@admin.register(SurveyAnswer)
class SurveyAnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'option', 'created_at')
    list_select_related = ('user', 'question', 'option')

admin.site.register(Banner)
admin.site.register(Raffle)
