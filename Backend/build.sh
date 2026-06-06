#!/usr/bin/env bash
# Build-команда для Render (выполняется при каждом деплое).
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py seed   # идемпотентно; можно убрать после первого деплоя
