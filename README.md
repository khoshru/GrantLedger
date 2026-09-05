# GrantLedger

GrantLedger is a secure Django application for managing temporary access requests, approvals, and access grants.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)

## Development

Install the locked dependencies and Git hooks:

```bash
uv sync --all-groups
uv run pre-commit install
```

Create the database and start Django:

```bash
uv run python manage.py migrate
uv run python manage.py runserver
```

Run all quality checks locally:

```bash
uv run pre-commit run --all-files
uv run python manage.py check
uv run pytest --cov
```

Production must provide `DJANGO_SECRET_KEY`. `DJANGO_DEBUG=true` enables debug
mode, and `DJANGO_ALLOWED_HOSTS` accepts a comma-separated host list.
