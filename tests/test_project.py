from django.test import Client
from django.urls import reverse


def test_admin_login_page(client: Client) -> None:
    response = client.get(reverse("admin:login"))

    assert response.status_code == 200
