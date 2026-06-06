# Pepsi Dunyosi — API-контракт

Базовый префикс: `/api/`. Формат — JSON. Авторизация — Telegram WebApp `initData`
(заголовок `X-Telegram-Init-Data`); в режиме разработки (`TELEGRAM_ALLOW_INSECURE=True`)
допускается `telegram_id` в теле/query.

## Авторизация
Все эндпоинты, кроме публичных списков, определяют пользователя так:
1. Заголовок `X-Telegram-Init-Data: <initData>` — подпись проверяется ботом.
2. Dev-фолбэк: `telegram_id` в теле (POST) или query (GET).

---

## Онбординг / Профиль (`/api/accounts/`)

| Метод | URL | Назначение | Тело / параметры |
|------|-----|-----------|------------------|
| GET  | `onboarding/` | Какой шаг показать | `telegram_id` → `{registered, policy_accepted, birth_year_set, survey_completed, next_step}` |
| POST | `register/` | Регистрация (идемпотентно) | `{name, phone, telegram_id?, ref?}` |
| POST | `policy/` | Принять соглашение | `{telegram_id?, accepted: true}` |
| POST | `birth-year/` | Год рождения (возраст ≥ 8) | `{telegram_id?, birth_year}` |
| GET  | `profile/` | Профиль + статистика | `telegram_id` |

`profile` отдаёт: `id, telegram_id, name, phone, balance, birth_year, policy_accepted,
survey_completed, codes_count, prizes_count, referrals_count, created_at`.
`ref` — telegram_id пригласившего (реферальная ссылка `?start=ref_<id>`).

## Главная (`/api/home/`)

| Метод | URL | Назначение |
|------|-----|-----------|
| GET  | `banners/` | Слайды карусели |
| GET  | `raffle/` | Активный розыгрыш (таймер): `{title, draw_at, recording_url}` |
| GET  | `survey/` | Вопросы опроса с вариантами |
| POST | `survey/submit/` | Пройти опрос (+250 ₽, один раз): `{telegram_id?, answers:[{question, option}]}` |

## Коды (`/api/codes/`)

| Метод | URL | Назначение |
|------|-----|-----------|
| POST | `submit/` | Отправить код: `{telegram_id?, code}` → `{entry:{status, reward...}, balance}`; статус `accepted`/`used`/`invalid`. Лимит 20/мин |
| GET  | `history/` | История + `{codes_sent, total_rubles, entries[]}` |

## Призы (`/api/prizes/`)

| Метод | URL | Назначение |
|------|-----|-----------|
| GET  | `` | Каталог призов («Все») |
| GET  | `my/?tab=won\|pending\|purchased` | Мои призы; `purchased` берётся из `shop.Purchase` |
| GET  | `stats/` | `{received, pending, purchases}` |

## Магазин (`/api/shop/`)

| Метод | URL | Назначение |
|------|-----|-----------|
| GET  | `products/` | Каталог товаров |
| POST | `buy/` | Купить: `{telegram_id?, product_id}` → `{purchase, balance}` (атомарно) |
| GET  | `my/` | Мои покупки |

---

## Запуск
```bash
pip install -r requirements.txt
cp .env.example .env          # заполнить TELEGRAM_BOT_TOKEN для прода
python manage.py migrate
python manage.py seed         # демо-данные
python manage.py runserver
```
