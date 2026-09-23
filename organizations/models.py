from typing import Any

from django.core.validators import RegexValidator
from django.db import models
from django.utils.text import slugify

NAME_MAX_LENGTH = 255
SLUG_MAX_LENGTH = 100


class Organization(models.Model):
    """A tenant that owns grants and ledger entries.

    Slug policy (the only supported workflow):

    1. If a slug is supplied at creation, it is used exactly as given
       (validated for format) and becomes immutable.
    2. Otherwise, a slug is generated once from the name with
       ``django.utils.text.slugify``. When the generated slug is already
       taken, a numeric suffix (``-2``, ``-3``, ...) is appended until it
       is free.
    3. The slug is never regenerated afterwards: renaming the organization
       does not change the slug, so external references remain stable.
    """

    name = models.CharField("Organization name", max_length=NAME_MAX_LENGTH)
    slug = models.CharField(
        "Organization slug",
        max_length=SLUG_MAX_LENGTH,
        unique=True,
        validators=[RegexValidator(regex=r"^[-a-zA-Z0-9_]+$")],
    )
    created_at = models.DateTimeField("Creation time", auto_now_add=True)

    class Meta:
        """Model metadata."""

        ordering = ["name"]
        verbose_name = "organization"

    def __str__(self) -> str:
        """Return a human-readable representation including the slug."""
        return f"{self.name} ({self.slug})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Generate a slug on first save only, per the documented policy."""
        if self._state.adding and not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self) -> str:
        """Derive a slug from the name, appending -2, -3, ... on collisions."""
        base = slugify(self.name)[:SLUG_MAX_LENGTH] or "organization"
        slug = base
        counter = 2
        while Organization.objects.filter(slug=slug).exists():
            suffix = f"-{counter}"
            slug = base[: SLUG_MAX_LENGTH - len(suffix)] + suffix
            counter += 1
        return slug
