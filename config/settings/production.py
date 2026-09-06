import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ImproperlyConfigured(f"{name} must be set")
    return value


SECRET_KEY = _required_env("DJANGO_SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS = [
    host.strip() for host in _required_env("DJANGO_ALLOWED_HOSTS").split(",")
]

SECURE_HSTS_SECONDS = 31_536_000
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405
