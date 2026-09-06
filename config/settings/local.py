from .base import *  # noqa: F403

SECRET_KEY = "django-insecure-local-development-only"  # nosec B105
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}
