import sys
import os
import json
from pathlib import Path
from django.conf import settings
import django

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

PROJECT_DIR = BASE_DIR / "RhymesOfLife"
sys.path.insert(0, str(PROJECT_DIR))

ENV_PATH = BASE_DIR / "environment.json"
with open(ENV_PATH) as f:
    environment = json.load(f)


settings.configure(
    SECRET_KEY=environment["SECRET_KEY"],
    DEBUG=environment["DEBUG"],
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': environment["DB_NAME"],
            'USER': environment["DB_USER"],
            'PASSWORD': environment["DB_PASSWORD"],
            'HOST': environment["DB_HOST"],
            'PORT': environment["DB_PORT"],
        }
    },
    INSTALLED_APPS=[
        'django.contrib.auth',
        'django.contrib.admin',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'base.apps.BaseConfig',
        'django_nyt',
    ],
    ROOT_URLCONF='RhymesOfLife.urls',
    SITE_ID=1,
    BASE_URL=environment.get("BASE_URL", "http://localhost:8000/"),
    DEFAULT_FROM_EMAIL=environment.get("DEFAULT_FROM_EMAIL", "Rhymes of Life <admin@igstan.com>"),
    MAILGUN_API_TOKEN=environment.get("MAILGUN_API_TOKEN"),
    MAILGUN_URL=environment.get("MAILGUN_URL"),
    TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_DIR, 'base', 'templates')],
        'APP_DIRS': True,
    }],
)

django.setup()
