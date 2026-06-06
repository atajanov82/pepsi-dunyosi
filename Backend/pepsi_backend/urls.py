from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # каждое приложение-страница подключается отдельно
    path('api/accounts/', include('accounts.urls')),  # профиль / регистрация
    path('api/home/',     include('home.urls')),       # главная
    path('api/codes/',    include('codes.urls')),       # коды
    path('api/prizes/',   include('prizes.urls')),      # призы
    path('api/shop/',     include('shop.urls')),        # магазин
]
