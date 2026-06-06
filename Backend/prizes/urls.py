from django.urls import path
from . import views

urlpatterns = [
    path('',       views.PrizeListView.as_view()),
    path('my/',    views.MyPrizesView.as_view()),
    path('stats/', views.PrizeStatsView.as_view()),
]
