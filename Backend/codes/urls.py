from django.urls import path
from . import views

urlpatterns = [
    path('submit/',  views.SubmitCodeView.as_view()),
    path('history/', views.CodeHistoryView.as_view()),
]
