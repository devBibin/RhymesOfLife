import os
import sys
from pathlib import Path

# Project root (folder with manage.py)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DJANGO_PACKAGE = PROJECT_ROOT / "RhymesOfLife"

# Ensure import paths
for p in (str(PROJECT_ROOT), str(DJANGO_PACKAGE)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Point Django to the real settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "RhymesOfLife.settings")

# Bootstrap Django
import django  # noqa: E402
django.setup()

# Re-export configured settings so legacy imports keep working
from django.conf import settings as dj_settings  # noqa: E402
settings = dj_settings
