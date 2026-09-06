from .base import *  # noqa: F403

SECRET_KEY = "django-insecure-tests-only"  # nosec B105
DEBUG = False
ALLOWED_HOSTS = ["testserver"]

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    },
}
