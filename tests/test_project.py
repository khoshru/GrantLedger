import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import Client
from django.urls import reverse


def test_admin_login_page(client: Client) -> None:
    response = client.get(reverse("admin:login"))

    assert response.status_code == 200


def test_production_settings_require_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DJANGO_SECRET_KEY", "production-test-key")
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "example.com, api.example.com")

    from config.settings import production

    assert production.DEBUG is False
    assert production.ALLOWED_HOSTS == ["example.com", "api.example.com"]

    monkeypatch.delenv("DJANGO_SECRET_KEY")
    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY must be set"):
        production._required_env("DJANGO_SECRET_KEY")
