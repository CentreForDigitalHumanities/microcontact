"""Container overrides for microcontact, driven by environment variables.

The regular development settings in microcontact.settings are left untouched;
this module only adapts the database, paths, secrets and hosts for the
container image. The container always uses PostgreSQL (like production).
"""

import os

from .settings import *  # noqa: F401,F403

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", SECRET_KEY)
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = [
    host for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if host
]

# Used by microcontact.views.proxy_maps (the /proxymaps endpoint).
GMAPIKEY = os.environ.get("GMAPIKEY", "")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.environ.get("DJANGO_DB_HOST", "db"),
        "PORT": os.environ.get("DJANGO_DB_PORT", "5432"),
        "NAME": os.environ.get("DJANGO_DB_NAME", "microcontact"),
        "USER": os.environ.get("DJANGO_DB_USER", "microcontact"),
        "PASSWORD": os.environ.get("DJANGO_DB_PASSWORD", ""),
    }
}
MEDIA_ROOT = os.environ.get("DJANGO_MEDIA_ROOT", "/app/media")
