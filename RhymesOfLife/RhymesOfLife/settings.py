from pathlib import Path
import json
import os

BASE_DIR = Path(__file__).resolve().parent.parent

with open(BASE_DIR / "../environment.json") as f:
    environment = json.loads(f.read())

SECRET_KEY = environment["SECRET_KEY"]
DEBUG = environment["DEBUG"]

ALLOWED_HOSTS = environment.get("ALLOWED_HOSTS", [])
CSRF_TRUSTED_ORIGINS = environment.get("CSRF_TRUSTED_ORIGINS", [])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",

    "base",
    "blog",

    "django.contrib.humanize.apps.HumanizeConfig",

    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",

    "modelcluster",
    "taggit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "base.middleware.user_language.SetUserLanguageMiddleware",
    "base.middleware.enforce_onboarding.EnforceOnboardingMiddleware",
    "base.middleware.banned_users.BannedUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]


STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"


ONBOARDING_REQUIRE_CONSENTS = True
ONBOARDING_REQUIRE_PHONE = True
ONBOARDING_SKIP_FOR_STAFF = True
ONBOARDING_REQUIRED_PROFILE_FIELDS = ("first_name", "last_name", "email", "birth_date")
ONBOARDING_DEFAULT_EXEMPT_PATHS_EXTRA = [
    "/admin/jsi18n/",
    "/static/admin/",
]


ONBOARDING_EXEMPT_URLNAMES = {
    "home_public",
    "login",
    "logout",
    "register",
    "verify_email",
    "request_verification",
    "verify_prompt",
    "connect_telegram",
    "phone_enter",
    "phone_wait",
    "phone_status_api",
    "phone_change",
    "consents",
    "profile_edit",
    "set_language",
    "admin:index",
}
ONBOARDING_EXEMPT_PATHS = set()

ROOT_URLCONF = "RhymesOfLife.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "base.context_processors.notifications",
                "base.context_processors.following_user_ids",
            ],
        },
    },
]

WSGI_APPLICATION = "RhymesOfLife.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": environment["DB_NAME"],
        "USER": environment["DB_USER"],
        "PASSWORD": environment["DB_PASSWORD"],
        "HOST": environment["DB_HOST"],
        "PORT": environment["DB_PORT"],
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru"
LANGUAGES = [
    ("en", "English"),
    ("ru", "Русский"),
]
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = environment.get("STATIC_ROOT", os.path.join(BASE_DIR, "staticfiles"))

MEDIA_URL = "/media/"
MEDIA_ROOT = environment.get("MEDIA_ROOT", os.path.join(BASE_DIR, "media"))

LOCALE_PATHS = [BASE_DIR / "locale"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.yandex.ru"
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = environment["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = environment["EMAIL_HOST_PASSWORD"]
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

MAILGUN_API_TOKEN = environment.get("MAILGUN_API_TOKEN")
MAILGUN_URL = environment.get("MAILGUN_URL")
MAILGUN_MAIL_DOAMIN = environment.get("MAILGUN_MAIL_DOAMIN")

DEFAULT_FROM_EMAIL = "Rhymes of Life <admin@igstan.com>"

PASSWORD_RESET_CODE_LENGTH = 6
PASSWORD_RESET_CODE_TTL_MIN = 15
PASSWORD_RESET_MAX_ATTEMPTS = 5
PASSWORD_RESET_RATE_LIMIT_PER_IP_MIN = 10
PASSWORD_RESET_RATE_LIMIT_PER_USER_MIN = 10

BASE_URL = environment.get("BASE_URL")

SITE_ID = 1

WAGTAIL_SITE_NAME = "Rhymes of Life"
WAGTAIL_I18N_ENABLED = False
WAGTAIL_CONTENT_LANGUAGES = [
    ("en", "English"),
    ("ru", "Russian"),
]
WAGTAILIMAGES_IMAGE_MODEL = "wagtailimages.Image"
WAGTAILIMAGES_MAX_UPLOAD_SIZE = 10 * 1024 * 1024
WAGTAILIMAGES_EXTENSIONS = ["gif", "jpg", "jpeg", "png", "webp"]
WAGTAILADMIN_BASE_URL = BASE_URL

EMAIL_VERIFICATION_EXEMPT_URLNAMES = {
    "login",
    "logout",
    "register",
    "home",
    "verify_email",
    "request_verification",
    "verify_prompt",
    "profile_onboarding",
    "set_language",
    "admin:index",
    "connect_telegram",
}
EMAIL_VERIFICATION_EXEMPT_PATHS = set()

TELEGRAM_BOT_TOKEN_ADMIN = environment.get("TELEGRAM_BOT_TOKEN_ADMIN")
_raw_chat_ids = environment.get("TELEGRAM_STAFF_CHAT_IDS", [])
if isinstance(_raw_chat_ids, str):
    TELEGRAM_STAFF_CHAT_IDS = [int(x) for x in _raw_chat_ids.split(",") if x.strip().lstrip("-").isdigit()]
else:
    TELEGRAM_STAFF_CHAT_IDS = [int(x) for x in _raw_chat_ids if str(x).lstrip("-").isdigit()]

TELEGRAM_BOT_TOKEN_USERS = environment.get("TELEGRAM_BOT_TOKEN_USERS", "")
TELEGRAM_BOT_USERNAME = environment.get("TELEGRAM_BOT_USERNAME", "")


SECURE_PROXY_SSL_HEADER = tuple(environment.get("SECURE_PROXY_SSL_HEADER", ())) or None
SESSION_COOKIE_SECURE = environment.get("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = environment.get("CSRF_COOKIE_SECURE", not DEBUG)
SECURE_SSL_REDIRECT = environment.get("SECURE_SSL_REDIRECT", False)

PUBLIC_KEY_CALL = environment.get("PUBLIC_KEY_CALL")
CAMPAIGN_ID = environment.get("CAMPAIGN_ID")
ZVONOK_API_INITIATE_URL = environment.get("ZVONOK_API_INITIATE_URL")
ZVONOK_API_POLLING_URL = environment.get("ZVONOK_API_POLLING_URL")
ZVONOK_STATIC_GATEWAY = environment.get("ZVONOK_STATIC_GATEWAY", "")
