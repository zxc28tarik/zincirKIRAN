# Development — Free Infrastructure Mode

Zincir Kıran does not require a paid cloud database during research development.

## Default development mode

- GitHub repository for version control
- GitHub Actions for CI
- PostgreSQL 16 for PIT schema validation
- Python 3.11 for research code

A remote Supabase project is optional and deferred.

## Local PostgreSQL

If Docker is installed:

```bash
docker compose up -d postgres
```

Apply the PIT schema:

```bash
PGPASSWORD=postgres psql \
  -h localhost \
  -U postgres \
  -d zincir_kiran \
  -v ON_ERROR_STOP=1 \
  -f supabase/schemas/pit_core.sql
```

Run SQL integrity checks:

```bash
PGPASSWORD=postgres psql \
  -h localhost \
  -U postgres \
  -d zincir_kiran \
  -v ON_ERROR_STOP=1 \
  -f tests/sql/pit_schema_smoke.sql
```

Run Python checks:

```bash
python -m pip install -e ".[dev]"
ruff check src tests
pytest -q
```

## Security

The database credentials above are local-development defaults only.

No production secret, API key, database password or paid-service credential belongs in Git.

The internal finance tables live under the `zk` schema. The schema is not granted to `PUBLIC`, `anon` or `authenticated` roles.

## Cloud deployment

Cloud deployment is deliberately not required for Implementation 1 acceptance.

If a remote database is introduced later, it must reproduce the same committed schema and pass the same PIT tests before it is trusted.
