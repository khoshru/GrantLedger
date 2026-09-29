import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client

from accounts.models import User
from organizations.models import Organization, OrganizationMembership


@pytest.mark.django_db
class TestOrganizationMembership:
    """Tests for the OrganizationMembership join model.

    Covers the three roles and their default, duplicate prevention at
    both the database and validation level, the CASCADE deletion policy,
    the reverse relationships (including the convenience ``users``
    many-to-many), memberships across multiple organizations, invalid
    roles through supported input paths, and the independence of
    organization roles from Django's ``is_staff``/``is_superuser`` flags.
    """

    def test_membership_save(self) -> None:
        """A membership persists and is the only row in the table."""
        org = Organization.objects.create(name="Redwood Trust")
        user = User.objects.create_user(email="alice@example.com", password="pw12345!")
        membership = OrganizationMembership.objects.create(organization=org, user=user)
        assert membership.pk is not None
        assert OrganizationMembership.objects.count() == 1

    def test_role_is_member(self) -> None:
        """A membership created without a role defaults to MEMBER."""
        org = Organization.objects.create(name="Redwood Trust")
        user = User.objects.create_user(email="bob@example.com", password="pw12345!")
        membership = OrganizationMembership.objects.create(organization=org, user=user)
        assert membership.role == OrganizationMembership.Role.MEMBER

    def test_each_role_saves(self) -> None:
        """Every defined role can be persisted within one organization."""
        org = Organization.objects.create(name="Redwood Trust")
        for index, role in enumerate(OrganizationMembership.Role):
            user = User.objects.create_user(
                email=f"r{index}@example.com", password="pw12345!"
            )
            OrganizationMembership.objects.create(
                organization=org, user=user, role=role
            )
        assert org.memberships.count() == 3
        assert (
            org.memberships.filter(role=OrganizationMembership.Role.ADMIN).count() == 1
        )

    def test_exactly_three_roles_defined(self) -> None:
        """The Role enum defines exactly MEMBER, APPROVER, and ADMIN."""
        assert [r.name for r in OrganizationMembership.Role] == [
            "MEMBER",
            "APPROVER",
            "ADMIN",
        ]

    def test_duplicate_membership_blocked_at_db_level(self) -> None:
        """Inserting a duplicate membership raises a database IntegrityError."""
        org = Organization.objects.create(name="Redwood Trust")
        user = User.objects.create_user(email="r@example.com", password="pw12345!")
        OrganizationMembership.objects.create(organization=org, user=user)
        with pytest.raises(IntegrityError), transaction.atomic():
            OrganizationMembership.objects.create(organization=org, user=user)

    def test_duplicate_membership_blocked_by_full_clean(self) -> None:
        """Model validation rejects a duplicate with a ValidationError."""
        org = Organization.objects.create(name="Redwood Trust")
        user = User.objects.create_user(email="r@example.com", password="pw12345!")
        OrganizationMembership.objects.create(organization=org, user=user)
        duplicate = OrganizationMembership(organization=org, user=user)
        with pytest.raises(ValidationError):
            duplicate.full_clean()

    def test_deleting_user_removes_membership(self) -> None:
        """Deleting a user cascades to their memberships."""
        org = Organization.objects.create(name="Redwood Trust")
        user = User.objects.create_user(email="r@example.com", password="pw12345!")
        OrganizationMembership.objects.create(organization=org, user=user)
        user.delete()
        assert not org.memberships.exists()

    def test_deleting_organization_removes_membership(self) -> None:
        """Deleting an organization cascades to memberships, keeping users."""
        org = Organization.objects.create(name="Redwood Trust")
        user = User.objects.create_user(email="r@example.com", password="pw12345!")
        OrganizationMembership.objects.create(organization=org, user=user)
        org.delete()
        assert OrganizationMembership.objects.count() == 0
        assert User.objects.filter(email="r@example.com").exists()

    def test_organization_exposes_users(self) -> None:
        """Organization.users exposes members through the join table."""
        org = Organization.objects.create(name="Redwood Trust")
        bob = User.objects.create_user(email="bob@example.com", password="12345pw")
        alice = User.objects.create_user(
            email="alice@example.com", password="pw12345pw"
        )
        OrganizationMembership.objects.create(
            organization=org, user=bob, role=OrganizationMembership.Role.ADMIN
        )
        OrganizationMembership.objects.create(organization=org, user=alice)
        assert set(org.users.all()) == {bob, alice}

    def test_user_across_multiple_organizations(self) -> None:
        """One user can hold different roles in different organizations."""
        redwood = Organization.objects.create(name="Redwood Trust")
        oak = Organization.objects.create(name="Oak")
        user = User.objects.create_user(email="alice@example.com", password="pw12345pw")
        OrganizationMembership.objects.create(
            organization=redwood, user=user, role=OrganizationMembership.Role.ADMIN
        )
        OrganizationMembership.objects.create(
            organization=oak, user=user, role=OrganizationMembership.Role.APPROVER
        )
        assert set(user.organizations.all()) == {redwood, oak}
        assert (
            user.organization_memberships.get(organization=redwood).role
            == OrganizationMembership.Role.ADMIN
        )
        assert (
            user.organization_memberships.get(organization=oak).role
            == OrganizationMembership.Role.APPROVER
        )

    def test_invalid_role_rejected_by_full_clean(self) -> None:
        """Model validation rejects a role outside the defined choices."""
        org = Organization.objects.create(name="Redwood Trust")
        user = User.objects.create_user(email="bad@example.com", password="pw12345!")
        membership = OrganizationMembership(organization=org, user=user, role="wizard")
        with pytest.raises(ValidationError):
            membership.full_clean()

    def test_invalid_role_rejected_by_admin_form(self, admin_client: Client) -> None:
        """The admin form rejects an invalid role without saving anything."""
        org = Organization.objects.create(name="Redwood Trust")
        user = User.objects.create_user(email="bad2@example.com", password="pw12345!")
        response = admin_client.post(
            "/admin/organizations/organizationmembership/add/",
            {
                "organization": org.pk,
                "user": user.pk,
                "role": "wizard",
            },
        )
        assert response.status_code == 200
        assert not OrganizationMembership.objects.exists()

    def test_admin_role_does_not_grant_django_flags(self) -> None:
        """An organization ADMIN role grants no Django-level flags."""
        org = Organization.objects.create(name="Redwood Trust")
        user = User.objects.create_user(
            email="orgadmin@example.com", password="pw12345!"
        )
        OrganizationMembership.objects.create(
            organization=org, user=user, role=OrganizationMembership.Role.ADMIN
        )
        user.refresh_from_db()
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_superuser_flag_does_not_change_membership_role(self) -> None:
        """A superuser still gets the default MEMBER role, not ADMIN."""
        org = Organization.objects.create(name="Oak Trust")
        user = User.objects.create_user(
            email="super@example.com", password="pw12345!", is_superuser=True
        )
        membership = OrganizationMembership.objects.create(organization=org, user=user)
        assert membership.role == OrganizationMembership.Role.MEMBER
