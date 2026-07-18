"""
Base Django settings for ShopCMS platform.
"""

from pathlib import Path

import environ

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environment
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    LOG_LEVEL=(str, "INFO"),
    OTP_USE_FIXED_CODE=(bool, False),
)

environ.Env.read_env(BASE_DIR / ".env")

# Security
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

LOCAL_APPS = [
    "core",
    "tenants",
    "accounts",
    "dashboard",
    "cms",
    "products",
    "carts",
    "addresses",
    "shipping",
    "payments",
    "orders",
    "taxes",
    "wishlists",
    "comments",
    "blog",
    "files",
    "notifications",
    "plugins",
    "digital",
    "subscriptions",
    "reports",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "core.middleware.security_headers.SecurityHeadersMiddleware",
    "core.middleware.rate_limit.APIRateLimitMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "tenants.middleware.TenantMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates", BASE_DIR],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "tenants.context_processors.store_context",
                "tenants.context_processors.theme_context",
                "cms.context_processors.cms_context",
            ],
            "builtins": [
                "tenants.templatetags.theme_tags",
                "tenants.templatetags.money_tags",
            ],
            "loaders": [
                "tenants.theme.loader.ThemeLoader",
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}

# Cache
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
        },
    }
}

# Celery
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/2")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Tehran"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60

# Cache TTL presets (seconds)
CACHE_DEFAULT_TTL = env.int("CACHE_DEFAULT_TTL", default=900)
CACHE_TTL_SHORT = env.int("CACHE_TTL_SHORT", default=300)
CACHE_TTL_MEDIUM = env.int("CACHE_TTL_MEDIUM", default=900)
CACHE_TTL_LONG = env.int("CACHE_TTL_LONG", default=3600)
CACHE_TTL_REPORTS = env.int("CACHE_TTL_REPORTS", default=600)
CACHE_TTL_PRODUCTS = env.int("CACHE_TTL_PRODUCTS", default=600)

# Backups
BACKUP_ROOT = BASE_DIR / "backups"
BACKUP_RETENTION_DAYS = env.int("BACKUP_RETENTION_DAYS", default=30)
BACKUP_INCLUDE_MEDIA_DEFAULT = env.bool("BACKUP_INCLUDE_MEDIA_DEFAULT", default=True)

# Security
RATE_LIMIT_ENABLED = env.bool("RATE_LIMIT_ENABLED", default=True)
RATE_LIMIT_API_ANON = env.int("RATE_LIMIT_API_ANON", default=120)
RATE_LIMIT_API_WINDOW = env.int("RATE_LIMIT_API_WINDOW", default=60)
SECURITY_HEADERS_ENABLED = env.bool("SECURITY_HEADERS_ENABLED", default=True)
AUDIT_LOG_RETENTION_DAYS = env.int("AUDIT_LOG_RETENTION_DAYS", default=90)
PLATFORM_NAME = env("PLATFORM_NAME", default="ShopCMS")

NINJA_DEFAULT_THROTTLE_RATES = {
    "anon": "120/min",
    "auth": "60/min",
    "otp_send": "5/min",
    "auth_refresh": "30/min",
}

# Celery Beat schedule
from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    "expire-subscriptions-daily": {
        "task": "core.tasks.expire_subscriptions",
        "schedule": crontab(hour=2, minute=0),
    },
    "cleanup-temp-files-hourly": {
        "task": "core.tasks.cleanup_temp_files",
        "schedule": crontab(minute=0),
    },
    "warm-cache-periodic": {
        "task": "core.tasks.warm_active_stores_cache",
        "schedule": crontab(hour="*/6", minute=15),
    },
    "backup-stores-nightly": {
        "task": "core.tasks.backup_active_stores",
        "schedule": crontab(hour=3, minute=30),
    },
    "cleanup-old-backups-weekly": {
        "task": "core.tasks.cleanup_old_backups",
        "schedule": crontab(hour=4, minute=0, day_of_week=0),
    },
    "cleanup-audit-logs-weekly": {
        "task": "core.tasks.cleanup_audit_logs",
        "schedule": crontab(hour=4, minute=30, day_of_week=0),
    },
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "fa-ir"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = env("STATIC_URL", default="/static/")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files
MEDIA_URL = env("MEDIA_URL", default="/media/")
MEDIA_ROOT = BASE_DIR / "media"

# Media uploads
FILE_UPLOAD_MAX_SIZE = env.int("FILE_UPLOAD_MAX_SIZE", default=10 * 1024 * 1024)
FILE_ALLOWED_MIME_PREFIXES = ("image/", "video/", "application/pdf")
FILE_THUMBNAIL_SIZES = {
    "thumb": (150, 150),
    "small": (320, 320),
    "medium": (640, 640),
    "large": (1280, 1280),
}

# Default primary key
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Multi-tenant
DEFAULT_STORE_SLUG = env("DEFAULT_STORE_SLUG", default="shop1")

# Auth
AUTH_USER_MODEL = "accounts.User"
OTP_USE_FIXED_CODE = env.bool("OTP_USE_FIXED_CODE", default=False)
OTP_FIXED_CODE = env("OTP_FIXED_CODE", default="12345")
OTP_RATE_LIMIT_SECONDS = env.int("OTP_RATE_LIMIT_SECONDS", default=60)
OTP_RATE_LIMIT_COUNT = env.int("OTP_RATE_LIMIT_COUNT", default=1)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@shopcms.local")

# Logging
LOG_LEVEL = env("LOG_LEVEL")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "shopcms.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "core": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "tenants": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "accounts": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "dashboard": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "products": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "carts": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "addresses": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "shipping": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "payments": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "cms": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "celery": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}
