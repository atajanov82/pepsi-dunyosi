from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Конфигурация из окружения (.env) ---
env = environ.Env(
    # Безопасные дефолты: если переменная не задана — берётся прод-безопасное значение.
    # Локальная разработка переопределяет их в .env (DEBUG=True, INSECURE=True и т.д.).
    DEBUG=(bool, False),
    SECRET_KEY=(str, 'dev-secret-key-change-in-production'),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
    CORS_ALLOWED_ORIGINS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
    TELEGRAM_BOT_TOKEN=(str, ''),
    # Определять пользователя по telegram_id из запроса без подписи Telegram —
    # только для локальной разработки. В проде ДОЛЖНО быть False (+ задан токен бота).
    TELEGRAM_ALLOW_INSECURE=(bool, False),
    # Максимальный возраст Telegram initData (сек) — защита от повторного использования.
    TELEGRAM_INITDATA_MAX_AGE=(int, 86400),
)
environ.Env.read_env(BASE_DIR / '.env')  # .env читается, если существует

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # сторонние
    'rest_framework',
    'corsheaders',
    # наши приложения (по страницам)
    'accounts',   # Профиль + регистрация + онбординг
    'home',       # Главная (баннеры, опрос, розыгрыш)
    'codes',      # Коды
    'prizes',     # Призы
    'shop',       # Магазин
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # отдача статики в проде (сразу после Security)
    'corsheaders.middleware.CorsMiddleware',  # как можно выше, до CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pepsi_backend.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

WSGI_APPLICATION = 'pepsi_backend.wsgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}')
}
# Переиспользуем подключения к БД между запросами (меньше задержка на дальнюю Neon).
# 0 = новое соединение каждый запрос (медленно). Через Neon-пулер 60с безопасно.
DATABASES['default']['CONN_MAX_AGE'] = env.int('CONN_MAX_AGE', default=60)

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# WhiteNoise: сжатая статика с манифестом (хеши в именах файлов)
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# --- Прод-безопасность (активируется при DEBUG=False) ---
CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS')
if not DEBUG:
    # Render терминирует HTTPS на прокси — доверяем заголовку X-Forwarded-Proto
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000           # 1 год
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# --- CORS (фронтенд на отдельном домене / Telegram WebApp) ---
CORS_ALLOWED_ORIGINS = env('CORS_ALLOWED_ORIGINS')
# В разработке разрешаем все источники, чтобы не мучиться с портами Vite/preview
CORS_ALLOW_ALL_ORIGINS = DEBUG and not CORS_ALLOWED_ORIGINS
# Разрешаем кастомный заголовок Telegram initData (иначе preflight внутри Telegram падает)
from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = (*default_headers, 'x-telegram-init-data')

# --- Telegram Mini-App ---
TELEGRAM_BOT_TOKEN = env('TELEGRAM_BOT_TOKEN')
TELEGRAM_ALLOW_INSECURE = env('TELEGRAM_ALLOW_INSECURE')
TELEGRAM_INITDATA_MAX_AGE = env('TELEGRAM_INITDATA_MAX_AGE')

# Дополнительные заголовки безопасности (применимы и в dev, и в prod)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# --- Бизнес-константы промо-акции (единый источник для всех приложений) ---
MIN_AGE = 8            # минимальный возраст участника (ТЗ: с 8 лет)
SURVEY_REWARD = 250    # ₽ за прохождение опроса (один раз)
REFERRAL_REWARD = 10   # ₽ пригласившему за каждого нового друга

# --- DRF ---
# Пользователь определяется через Telegram initData (см. accounts/authentication.py),
# с dev-фолбэком на telegram_id из запроса при TELEGRAM_ALLOW_INSECURE.
# Browsable API только в DEBUG (в проде — лишняя поверхность/раскрытие).
_RENDERERS = ['rest_framework.renderers.JSONRenderer']
if DEBUG:
    _RENDERERS.append('rest_framework.renderers.BrowsableAPIRenderer')

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_RENDERER_CLASSES': _RENDERERS,
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.ScopedRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {
        'code_submit': '20/min',   # перебор промокодов
        'register': '30/min',      # спам регистраций / фрод рефералов
        'buy': '60/min',
        'survey': '10/min',
    },
}
