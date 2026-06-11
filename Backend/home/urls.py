from django.urls import path
from . import views

urlpatterns = [
    path('banners/',       views.BannerListView.as_view()),
    path('raffle/',        views.ActiveRaffleView.as_view()),
    path('raffles/',       views.RaffleListView.as_view()),
    path('survey/',        views.SurveyView.as_view()),
    path('survey/submit/', views.SubmitSurveyView.as_view()),
]
