from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BASE_DIR.parent
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(REPO_DIR / ".env")
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "app.apps.AppConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]
ROOT_URLCONF = "Project.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
WSGI_APPLICATION = "Project.wsgi.application"
ASGI_APPLICATION = "Project.asgi.application"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST", default="127.0.0.1"),
        "PORT": env.int("POSTGRES_PORT", default=5432),
        "CONN_MAX_AGE": env.int("DB_CONN_MAX_AGE", default=60),
        "OPTIONS": {"connect_timeout": 5},
    }
}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation." + name}
    for name in [
        "UserAttributeSimilarityValidator",
        "MinimumLengthValidator",
        "CommonPasswordValidator",
        "NumericPasswordValidator",
    ]
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = REPO_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
PRIVATE_UPLOAD_ROOT = REPO_DIR / "var" / "uploads"
CSV_MAX_BYTES = env.int("CSV_MAX_BYTES", default=10 * 1024 * 1024)
CSV_MAX_ROWS = env.int("CSV_MAX_ROWS", default=100_000)
CSV_MAX_COLUMNS = env.int("CSV_MAX_COLUMNS", default=100)
CSV_PREVIEW_ROWS = env.int("CSV_PREVIEW_ROWS", default=10)
CSV_MAX_FILES = env.int("CSV_MAX_FILES", default=5)
DATA_UPLOAD_MAX_NUMBER_FILES = CSV_MAX_FILES
# Django spools large uploads to temporary disk rather than holding all in memory.
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=not DEBUG)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Optional until AI features are invoked; uploads work without an API key.
GEMINI_API_KEY = env("GEMINI_API_KEY", default="")
GEMINI_MODEL = env("GEMINI_MODEL", default="")
GEMINI_TIMEOUT_SECONDS = env.int("GEMINI_TIMEOUT_SECONDS", default=30)
GEMINI_MAX_OUTPUT_TOKENS = env.int("GEMINI_MAX_OUTPUT_TOKENS", default=4096)
GEMINI_TEMPERATURE = env.float("GEMINI_TEMPERATURE", default=0.1)
ANALYSIS_TIMEOUT_SECONDS = env.int("ANALYSIS_TIMEOUT_SECONDS", default=20)
ANALYSIS_MAX_RESULT_ROWS = env.int("ANALYSIS_MAX_RESULT_ROWS", default=200)
ANALYSIS_MEMORY_MB = env.int("ANALYSIS_MEMORY_MB", default=256)
