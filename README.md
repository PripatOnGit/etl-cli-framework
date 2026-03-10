# etl-cli-framework

![CI](https://github.com/YOUR_USERNAME/etl-cli-framework/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/YOUR_USERNAME/YOUR_GIST_ID/raw/coverage.json)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker)
![License](https://img.shields.io/badge/license-MIT-green)

A production-grade, configurable command-line ETL tool built from scratch in Python.

Zero hardcoded business logic — all transformation rules live in a YAML config file.
Every record is validated against a JSON Schema. Bad records are logged with field-level
detail and never silently dropped. Identical environments from dev laptop to CI to prod
via Docker.

---

## Features

| Feature | Details |
|---|---|
| **Sources** | CSV, JSON, REST API (with exponential backoff retry), SQLite |
| **Targets** | SQLite (dev), PostgreSQL via Docker (test/prod) |
| **Validation** | JSON Schema — collects ALL field errors per record, not just first |
| **Transforms** | Column renames, type casts, row filters — all in YAML, zero Python |
| **Logging** | Structured JSON with correlation IDs and per-run summaries |
| **Error routing** | Bad records → error log with field + rule + value. Never dropped silently |
| **Upsert** | Safe reruns — updates existing records, inserts new ones |
| **Testing** | pytest with >80% coverage enforced, fixtures, mocks, integration tests |
| **CI/CD** | GitHub Actions — lint → test → coverage badge auto-updates on every push |

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/priyu/etl-cli-framework.git
cd etl-cli-framework
make install

# 2. Run a dry-run (no data written)
etl --source csv --target sqlite --env dev --dry-run

# 3. Validate only — check data quality without loading
etl --source csv --target sqlite --validate-only --config config/pipeline.yaml

# 4. Full pipeline run
etl --source csv --target sqlite --env dev --config config/pipeline.yaml
```

### With Docker

```bash
# Start PostgreSQL
docker-compose up -d

# Run full test suite inside container
make docker-test

# Run ETL against Dockerised Postgres
etl --source csv --target postgres --env test --config config/pipeline.yaml
```

---

## CLI Reference

```
Usage: etl [OPTIONS]

  ETL CLI — Extract, validate, transform, and load data.

Options:
  --source          [csv|json|api|sqlite]   Input source type          [required]
  --target          [sqlite|postgres]       Output target type         [required]
  --env             [dev|test|prod]         Runtime environment        [default: dev]
  --dry-run                                 Run pipeline, write nothing
  --validate-only                           Stop after validation step
  --config          PATH                    Path to YAML pipeline config
                                            [default: config/pipeline.yaml]
  --help                                    Show this message and exit
```

---

## Sample Output

A successful run with one invalid record:

```json
{"timestamp":"2024-01-15T14:32:01Z","level":"INFO","message":"Pipeline started",
 "correlation_id":"a3f2-4b91","source":"csv","target":"sqlite","env":"dev"}

{"timestamp":"2024-01-15T14:32:01Z","level":"INFO","message":"Stage complete",
 "correlation_id":"a3f2-4b91","stage":"extract","duration_secs":0.043}

{"timestamp":"2024-01-15T14:32:02Z","level":"WARNING","message":"Validation failed",
 "correlation_id":"a3f2-4b91","record_index":7,"field":"salary",
 "rule":"minimum","value":-500}

{"timestamp":"2024-01-15T14:32:02Z","level":"INFO","message":"Stage complete",
 "correlation_id":"a3f2-4b91","stage":"validate","duration_secs":0.187}

{"timestamp":"2024-01-15T14:32:03Z","level":"INFO","message":"Run complete",
 "correlation_id":"a3f2-4b91","status":"success","total_records":1000,
 "valid_records":998,"invalid_records":2,"loaded_records":998,
 "duration_secs":1.23,"errors_by_field":{"salary":2}}
```

Every log line is a single JSON object — grep, pipe to `jq`, or ingest into Datadog/CloudWatch/ELK directly.

---

## Configuration

All pipeline behaviour is defined in `config/pipeline.yaml`. No Python changes needed to modify business rules.

```yaml
# config/pipeline.yaml
source:
  type: csv
  path: data/input.csv
  encoding: utf-8

target:
  type: sqlite
  path: data/etl_output.db
  table: processed_records

transformations:
  rename_columns:
    first_name: given_name        # rename column in output
    emp_id: employee_id
  type_casts:
    salary: float                 # cast string → float
    hire_date: datetime
    age: int
  filters:
    - column: age
      operator: gte               # greater than or equal
      value: 18
    - column: status
      operator: eq
      value: active

validation:
  schema_file: config/schema.json
  on_error: log_and_skip          # log_and_skip | fail_fast
```

### JSON Schema

Define what a valid record looks like in `config/schema.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["employee_id", "given_name", "salary", "hire_date"],
  "properties": {
    "employee_id": { "type": "string", "pattern": "^EMP[0-9]{4}$" },
    "given_name":  { "type": "string", "minLength": 1, "maxLength": 100 },
    "salary":      { "type": "number", "minimum": 0 },
    "hire_date":   { "type": "string", "format": "date" }
  },
  "additionalProperties": false
}
```

---

## Architecture

```
┌──────────────┐     ┌───────────────┐     ┌───────────────┐     ┌──────────────┐
│    Source    │     │   Validator   │     │  Transformer  │     │    Target    │
│   (Reader)   │────▶│  JSON Schema  │────▶│  YAML Config  │────▶│   (Writer)   │
│ CSV/API/DB   │     │  Bad→ErrorLog │     │ rename/cast/  │     │ SQLite / PG  │
└──────────────┘     └───────────────┘     │    filter     │     └──────────────┘
                                           └───────────────┘
       │                    │                     │                     │
       └────────────────────┴─────────────────────┴─────────────────────┘
                                         │
                              ┌──────────▼──────────┐
                              │    ETLLogger (JSON)  │
                              │  correlation_id on   │
                              │    every log line    │
                              │  RunSummary on exit  │
                              └─────────────────────┘
```

### Project Structure

```
etl-cli-framework/
├── src/etl/
│   ├── cli.py                  # Click entry point — all 6 flags
│   ├── config_loader.py        # YAML loader with required-key validation
│   ├── logger.py               # JsonFormatter, ETLLogger, RunSummary, timed_stage
│   ├── reader/
│   │   ├── base.py             # Abstract BaseReader — enforces read() contract
│   │   ├── csv_reader.py       # pandas read_csv with safe defaults
│   │   ├── api_reader.py       # requests + tenacity @retry + json_normalize
│   │   └── factory.py          # get_reader(type, config) — no if/elif in CLI
│   ├── validator/
│   │   └── schema_validator.py # Draft7Validator.iter_errors — all errors per record
│   ├── transform/
│   │   └── transformer.py      # apply_renames, apply_filters, apply_type_casts
│   └── writer/
│       ├── base.py             # Abstract BaseWriter — enforces write() contract
│       ├── engine.py           # SQLAlchemy engine factory — SQLite or Postgres
│       ├── sqlite_writer.py    # Dev writer — chunked inserts, upsert support
│       └── postgres_writer.py  # Prod writer — staging table upsert pattern
├── tests/
│   ├── conftest.py             # Shared fixtures — auto-available to all test files
│   ├── test_cli.py
│   ├── test_config_loader.py
│   ├── test_schema_validator.py
│   ├── test_csv_reader.py
│   ├── test_api_reader.py      # All API calls mocked — no real HTTP in tests
│   ├── test_sqlite_writer.py   # In-memory SQLite — fast and isolated
│   └── test_pipeline_integration.py  # Full CSV → validate → transform → SQLite
├── config/
│   ├── pipeline.yaml           # All pipeline rules — no business logic in Python
│   └── schema.json             # What a valid record looks like
├── data/
│   ├── sample_input.csv        # Sample data to run the pipeline
│   └── bad_records.json        # Intentionally invalid data for testing validator
├── .github/workflows/
│   └── ci.yml                  # lint → test → coverage badge on every push
├── Dockerfile                  # Non-root user, layer-cached, production image
├── docker-compose.yml          # Postgres + ETL app, healthcheck, named volumes
├── Makefile                    # make install / test / lint / coverage / docker-build
├── pyproject.toml              # Package config, tool settings, CLI entrypoint
├── requirements.txt            # Runtime dependencies only
├── requirements-dev.txt        # pytest, black, flake8, isort, detect-secrets
└── .pre-commit-config.yaml     # black + flake8 + isort + detect-secrets on commit
```

### Design Decisions

**Why YAML config over hardcoded transforms?**
Business rules change often. Putting them in YAML means zero code change and zero deployment
when a rule changes. A data analyst can modify pipeline behaviour without touching Python,
creating a PR, or waiting for a deployment cycle.

**Why JSON Schema over custom validation functions?**
JSON Schema is a standard — non-engineers can read and edit it. It's declarative: you describe
what valid looks like, not how to check it. `Draft7Validator.iter_errors()` collects every
validation failure per record, not just the first. This means one pass reveals all broken
fields in one log line.

**Why SQLAlchemy over raw SQL?**
The same writer code works for SQLite and PostgreSQL. Only the connection string changes
between environments. `pool_pre_ping=True` self-heals stale connections in long-running
jobs without any manual reconnect logic.

**Why structured JSON logging?**
Plain text logs can't be searched programmatically. JSON logs can be ingested by Datadog,
CloudWatch, ELK Stack, or Grafana Loki and filtered by any field. The `correlation_id`
field links every log line from a single run together — one grep returns the complete
history of that run.

---

## Development

### Prerequisites

- Python 3.11+
- Docker + Docker Compose
- Git

### Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# Install all dependencies and register CLI entrypoint
make install

# Verify installation
etl --help
```

### Environment Variables

Copy `.env.example` to `.env` and fill in values. Never commit `.env`.

```bash
cp .env.example .env
```

```env
# .env.example
DB_HOST=localhost
DB_PORT=5432
DB_NAME=etl_db
DB_USER=etl_user
DB_PASSWORD=change_me

OPENWEATHER_API_KEY=your_key_here

ETL_ENV=dev
ETL_LOG_LEVEL=INFO
ETL_CONFIG_PATH=config/pipeline.yaml
```

### Make Targets

```bash
make install       # install deps + pre-commit hooks
make lint          # black + isort + flake8
make test          # run unit tests (fast, no I/O)
make test-all      # run all tests including integration
make coverage      # tests + HTML coverage report → open htmlcov/index.html
make docker-build  # build Docker image
make docker-test   # run full suite inside container
make clean         # remove __pycache__, .coverage, htmlcov, dist
```

---

## Testing

```bash
# Run all tests
pytest

# Run unit tests only (no DB or file I/O)
pytest -m unit

# Run with coverage report
pytest --cov=src/etl --cov-report=term-missing

# Run integration tests (requires Docker Postgres running)
docker-compose up -d
pytest -m integration
```

### Test Structure

- **Unit tests** — every function tested in isolation. External calls (HTTP, DB) are mocked.
- **Integration tests** — full pipeline: CSV → validate → transform → in-memory SQLite.
- **Coverage threshold** — `--cov-fail-under=80` enforced in CI. Build fails if coverage drops.
- **Fixtures** — shared in `conftest.py`. Uses `tmp_path` (built-in) for file tests and
  in-memory SQLite for DB tests. No cleanup needed.

---

## CI/CD

GitHub Actions runs on every push to `main` and every pull request:

```
push / PR
    │
    ▼
┌─────────┐     passes     ┌──────────────┐     passes     ┌──────────────┐
│  lint   │──────────────▶ │ test+coverage│──────────────▶ │ update badge │
│ black   │                │ pytest       │                │ main only    │
│ isort   │                │ --cov ≥ 80%  │                └──────────────┘
│ flake8  │                │ + Postgres   │
└─────────┘                │   sidecar    │
                           └──────────────┘
```

A PostgreSQL container runs as a service sidecar during the test job — integration tests
run against a real database in CI, identical to local Docker setup.

---

## Stack

| Layer | Technology | Why |
|---|---|---|
| CLI | Click 8.x | Decorator-based flags, auto --help, CliRunner for tests |
| Data processing | pandas 2.x | DataFrame as universal pipeline currency |
| Validation | jsonschema 4.x | Declarative, standard, iter_errors for all failures |
| Config | PyYAML 6.x | safe_load only — never executes arbitrary code |
| DB ORM | SQLAlchemy 2.x | One codebase for SQLite + PostgreSQL |
| HTTP | requests + tenacity | Exponential backoff retry on network errors |
| Testing | pytest + pytest-mock | Fixtures, parametrize, mocker.patch |
| Formatting | black + isort | Zero-config, enforced at commit via pre-commit |
| Linting | flake8 | Catches bugs and style issues before review |
| Secrets | detect-secrets | Blocks credential commits at pre-commit stage |
| Containers | Docker + Compose | Identical environment dev → CI → prod |
| CI/CD | GitHub Actions | Lint → test → badge on every push |

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full version history.

### v1.0.0 — 2026-03-11

- Click CLI with all 6 flags: `--source`, `--target`, `--env`, `--dry-run`, `--validate-only`, `--config`
- CSV reader with configurable encoding and delimiter
- REST API reader with exponential backoff retry via tenacity
- JSON Schema validator with `iter_errors` — all field failures per record
- YAML config loader — column renames, type casts, row filters
- SQLite writer with chunked inserts and upsert support
- PostgreSQL writer with staging table upsert pattern
- Structured JSON logger with correlation IDs and RunSummary
- `errors_by_field` tracking across the full pipeline run
- pytest suite: unit + integration tests, >80% coverage enforced
- GitHub Actions CI: lint → test → coverage badge
- Dockerfile + docker-compose.yml with healthcheck and named volumes
- Makefile with `install`, `lint`, `test`, `coverage`, `docker-build` targets
