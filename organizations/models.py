import re
from typing import Any

from django.core.validators import RegexValidator
from django.db import IntegrityError, models, transaction
from django.utils.text import slugify

NAME_MAX_LENGTH = 255
SLUG_MAX_LENGTH = 100
MAX_GENERATION_ATTEMPTS = 5


class Organization(models.Model):
    """A tenant that owns grants and ledger entries.

    Slug policy (the only supported workflow):

    1. If a slug is supplied at creation, it is used exactly as given
       (validated for format) and becomes immutable.
    2. Otherwise, a slug is generated once from the name with
       ``django.utils.text.slugify``. When the generated slug is already
       taken, a numeric suffix (``-2``, ``-3``, ...) is appended until it
       is free. If a concurrent create takes the generated slug first,
       generation is retried (bounded by MAX_GENERATION_ATTEMPTS).
    3. The slug is never regenerated afterwards: renaming the organization
       does not change the slug, so external references remain stable.
    4. Slug *format* is validated by ``full_clean()`` / admin forms only;
       the ORM does not run validators, so code using ``objects.create()``
       must pass a well-formed slug.
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
            self._save_with_generated_slug(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def _generate_unique_slug(self) -> str:
        """Derive a slug from the name, appending -2, -3, ... on collisions."""
        base = slugify(self.name)[:SLUG_MAX_LENGTH] or "organization"
        prefix = base[: SLUG_MAX_LENGTH - 12]
        taken = set(
            Organization.objects.filter(slug__startswith=prefix).values_list(
                "slug", flat=True
            )
        )
        if base not in taken:
            return base

        used = [int(m.group(1)) for s in taken if (m := re.fullmatch(r".*-(\d+)", s))]
        counter = max(used, default=1) + 1
        suffix = f"-{counter}"
        return base[: SLUG_MAX_LENGTH - len(suffix)] + suffix

    def _save_with_generated_slug(self, *args: Any, **kwargs: Any) -> None:
        for attempts in range(1, MAX_GENERATION_ATTEMPTS + 1):
            self.slug = self._generate_unique_slug()
            try:
                with transaction.atomic():
                    super().save(*args, **kwargs)
                return
            except IntegrityError:
                if attempts == MAX_GENERATION_ATTEMPTS:
                    raise
