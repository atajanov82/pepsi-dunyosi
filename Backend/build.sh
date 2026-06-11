#!/usr/bin/env bash
# Build-команда для Render (выполняется при каждом деплое).
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py seed   # идемпотентно; можно убрать после первого деплоя

# Суперпользователь из переменных окружения (идемпотентно: создаёт или обновляет пароль).
# Задайте на Render: DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_PASSWORD (и при желании EMAIL).
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
U = get_user_model()
u = os.environ.get('DJANGO_SUPERUSER_USERNAME')
p = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
e = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
if u and p:
    obj, created = U.objects.get_or_create(username=u, defaults={'email': e})
    obj.is_staff = True; obj.is_superuser = True; obj.set_password(p); obj.save()
    print('superuser ready:', u, '(created)' if created else '(updated)')
else:
    print('superuser env vars not set — skip')
"
