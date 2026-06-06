from django.urls import path
from . import views

urlpatterns = [
    path('register/',   views.RegisterView.as_view()),
    path('profile/',    views.ProfileView.as_view()),
    path('onboarding/', views.OnboardingStatusView.as_view()),
    path('policy/',     views.AcceptPolicyView.as_view()),
    path('birth-year/', views.BirthYearView.as_view()),
]
