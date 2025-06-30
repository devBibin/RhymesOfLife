import sys
import os
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(BASE_DIR / "RhymesOfLife"))

with open(BASE_DIR / "environment.json") as f:
    environment = json.loads(f.read())

from django.conf import settings

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
        'django.contrib.contenttypes',
        'base.apps.BaseConfig',
    ],
    DOMAIN=environment.get("DOMAIN", "app.igstan.com"),
    MAILGUN_API_TOKEN=environment.get("MAILGUN_API_TOKEN"),
    MAILGUN_URL=environment.get("MAILGUN_URL"),
)

import django
django.setup()


from base.models import User, AdditionalUserInfo
print("✅ ORM connector initialized successfully!")