# GrantLedger

GrantLedger is a secure Django application for managing temporary access requests, approvals, and access grants.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/) 0.12.10 or newer

## Local Setup

Install Python, the locked dependencies, and the Git hooks:

```bash
uv python install 3.14
UV_MALWARE_CHECK=1 uv sync --locked --all-groups --preview-features malware-check
uv run pre-commit install
```

Create the database and start the server:

```bash
uv run python manage.py migrate
uv run python manage.py runserver
```

The application is available at <http://127.0.0.1:8000/>.

## Quality Checks

```bash
uv run pre-commit run --all-files
uv run python manage.py check
uv run pytest --cov
```

Pre-commit runs formatting, linting, type checking, Bandit, and dependency
auditing automatically on each commit. Tests enforce a minimum of 85% branch
coverage.

## Contributing

Create a focused branch, add tests with your change, run the quality checks,
and open a pull request against `main`. CI must pass before the change is
merged.

Local commands use `config.settings.local` automatically. Deployments use
`config.settings.production` and must provide `DJANGO_SECRET_KEY` and the
comma-separated `DJANGO_ALLOWED_HOSTS` through their environment.
