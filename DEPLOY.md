# Деплой Pepsi Dunyosi (тестовый стенд)

Стек: **Neon** (Postgres) → **Render** (бэкенд Django + gunicorn + WhiteNoise) → **Cloudflare Pages** (фронт).

Порядок: сначала БД, потом бэкенд, потом фронт, в конце связываем CORS и Telegram.

---

## 0. Подготовка: залить код на GitHub
Render и Cloudflare тянут код из репозитория.
```bash
cd Pepsi_backend
git init
git add .
git commit -m "Pepsi Dunyosi"
git branch -M main
git remote add origin https://github.com/<you>/pepsi.git
git push -u origin main
```
`.env` и `db.sqlite3` не попадут (см. Backend/.gitignore).

---

## 1. Neon — база данных
1. https://neon.tech → Create project (регион поближе).
2. Скопировать **connection string**, вид:
   `postgresql://user:pass@ep-xxx.eu-central-1.aws.neon.tech/neondb?sslmode=require`
3. Сохранить — это `DATABASE_URL` для Render. `?sslmode=require` обязателен.

---

## 2. Render — бэкенд
**Вариант А (Blueprint):** New → Blueprint → выбрать репозиторий → Render прочитает `render.yaml`.
**Вариант Б (вручную):** New → Web Service → репозиторий, затем:
- Root Directory: `Backend`
- Build Command: `bash build.sh`
- Start Command: `gunicorn pepsi_backend.wsgi:application --bind 0.0.0.0:$PORT`

**Environment Variables** (Render → Environment):
| Ключ | Значение |
|------|----------|
| `PYTHON_VERSION` | `3.12.7` |
| `SECRET_KEY` | длинная случайная строка (или Generate) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `.onrender.com` |
| `DATABASE_URL` | строка из Neon (с `?sslmode=require`) |
| `TELEGRAM_BOT_TOKEN` | токен бота (см. §5); для теста можно пустым |
| `TELEGRAM_ALLOW_INSECURE` | `True` для теста в браузере, `False` — только Telegram |
| `CORS_ALLOWED_ORIGINS` | заполнить после §4 (URL Cloudflare) |
| `CSRF_TRUSTED_ORIGINS` | то же, что CORS |

Деплой запустит `build.sh`: install → collectstatic → migrate → seed (демо-данные).
Бэкенд будет на `https://<имя>.onrender.com`. Проверка: открыть
`https://<имя>.onrender.com/api/home/banners/` — должен вернуться JSON.

Админка: `https://<имя>.onrender.com/admin/`. Создать админа — Render → Shell:
`python manage.py createsuperuser`.

> ⚠️ Free-план Render «засыпает» — первый запрос после простоя идёт ~30–50 сек.

---

## 3. Указать фронту адрес бэкенда
В `Frontened/public/config.js` раскомментировать и вписать URL Render:
```js
window.PEPSI_API_BASE = 'https://<имя>.onrender.com/api';
```
Закоммитить и запушить.

---

## 4. Cloudflare Pages — фронт
1. https://dash.cloudflare.com → Workers & Pages → Create → Pages → Connect to Git.
2. Выбрать репозиторий. Настройки сборки:
   - Framework preset: **None**
   - Build command: *(пусто)*
   - **Build output directory: `Frontened/public`**
3. Deploy. Получите `https://<проект>.pages.dev`.
4. Приложение: `https://<проект>.pages.dev/pepsi.html`.

Затем вернуться в Render и заполнить:
- `CORS_ALLOWED_ORIGINS = https://<проект>.pages.dev`
- `CSRF_TRUSTED_ORIGINS = https://<проект>.pages.dev`
→ Render передеплоит. Без этого браузер заблокирует запросы (CORS).

---

## 5. Telegram-бот (для реального Mini-App)
1. @BotFather → `/newbot` → получить токен → в Render `TELEGRAM_BOT_TOKEN`.
2. @BotFather → Bot Settings → Menu Button / Web App → URL =
   `https://<проект>.pages.dev/pepsi.html`.
3. Для боевой авторизации поставить `TELEGRAM_ALLOW_INSECURE=False` —
   тогда пользователь определяется только по подписи Telegram `initData`.

**Тест без Telegram:** оставьте `TELEGRAM_ALLOW_INSECURE=True` и открывайте
`pages.dev/pepsi.html` прямо в браузере — работает на dev-идентификаторе.

---

## Проверка после деплоя
- `GET /api/home/banners/` отдаёт JSON ✓
- На `pages.dev/pepsi.html` проходит онбординг, вводятся коды, виден баланс ✓
- В DevTools → Network нет ошибок CORS ✓

## Про JWT
`djangorestframework-simplejwt` есть в зависимостях, но API использует
Telegram `initData` (штатный механизм Mini-App), а не JWT-сессии. Отдельный
вход по логину/паролю для промо-приложения не нужен; админка Django — по сессии.
