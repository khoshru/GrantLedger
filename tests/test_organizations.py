import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client
from django.utils import timezone

from organizations.models import Organization

NAME_MAX_LENGTH = 255
SLUG_MAX_LENGTH = 100


@pytest.mark.django_db
class TestOrganizationCreation:
    def test_create_with_generated_slug(self) -> None:
        org = Organization.objects.create(name="Redwood Grant Trust!")
        assert org.slug == "redwood-grant-trust"

    def test_create_unique_slug(self) -> None:
        Organization.objects.create(name="acme Crop", slug="acme")
        with pytest.raises(IntegrityError), transaction.atomic():
            Organization.objects.create(name="other acme", slug="acme")

    def test_create_required_name(self) -> None:
        org = Organization(name="", slug="acme")
        with pytest.raises(ValidationError):
            org.full_clean()

    def test_create_required_slug(self) -> None:
        org = Organization(name="acme", slug="")
        with pytest.raises(ValidationError):
            org.full_clean()

    def test_auto_fill_timestamp(self) -> None:
        before = timezone.now()
        org = Organization.objects.create(name="Redwood Grant Trust!")
        after = timezone.now()
        assert org.created_at is not None
        assert before <= org.created_at <= after

    def test_collision_gets_suffix(self) -> None:
        first = Organization.objects.create(name="Acme Crop")
        second = Organization.objects.create(name="Acme Crop")
        assert first.slug == "acme-crop"
        assert second.slug == f"{first.slug}-2"

    def test_str_representation(self) -> None:
        org = Organization(name="Acme Crop", slug="acme")
        assert str(org) == "Acme Crop (acme)"

    def test_create_supplied_slug(self) -> None:
        org = Organization.objects.create(name="Acme Crop", slug="custom-slip")
        assert org.slug == "custom-slip"

    def test_slug_stable_on_rename(self) -> None:
        org = Organization.objects.create(name="Acme Crop")
        saved_slug = org.slug
        org.name = "Renamed Trust"
        org.save()
        org.refresh_from_db()
        assert org.slug == saved_slug
        assert org.name == "Renamed Trust"

    def test_long_name_slug_truncated(self) -> None:
        org = Organization.objects.create(name="a" * 250)
        assert len(org.slug) == SLUG_MAX_LENGTH

    def test_admin_lists_organizations(self, admin_client: Client) -> None:
        Organization.objects.create(name="Visible Crop", slug="visible")
        response = admin_client.get("/admin/organizations/organization/")
        assert response.status_code == 200
        assert "Visible Crop" in response.content.decode()
