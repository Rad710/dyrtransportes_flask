# CLAUDE.md - DYR Transportes Flask Backend

## Project Overview

DYR Transportes is a transportation management system backend built with Flask and MySQL. It serves as a REST API for managing shipments, drivers, routes, products, payrolls, and related business operations for a freight/logistics company. The frontend is a separate React application served as static files.

## Tech Stack

- **Language:** Python 3.13+
- **Framework:** Flask 3.1
- **Database:** MySQL 8+ / 9+ via `mysqlclient`
- **ORM:** SQLAlchemy 2.0 (Mapped column style)
- **Migrations:** Alembic 1.17
- **Auth:** PyJWT (HS256 JWT tokens)
- **Excel Export:** openpyxl
- **PDF Export:** LibreOffice headless (`soffice`), converts the Excel exports
- **Localization:** num2words (Spanish number-to-word conversion)
- **Production Server:** uWSGI
- **Type Checking:** mypy
- **Linting:** pylint

## Project Structure

```
dyrtransportes_flask/
├── CLAUDE.md
├── README.md
├── wsgi.py                          # uWSGI entry point, adds src/ to sys.path
├── requirements-common.txt          # Shared dependencies (Flask, SQLAlchemy, etc.)
├── requirements-dev.txt             # Dev-only deps (mypy, pylint)
├── requirements-prod.txt            # Prod-only deps (uWSGI)
├── .env                             # Environment variables (gitignored)
├── docker/
│   └── Dockerfile                   # Production image (python:3.13-slim-bookworm)
├── deploy/
│   ├── docker-compose.prod.yml      # Prod: Flask + MySQL + Adminer stack
│   ├── docker-compose.demo.yml      # Public demo: shared MySQL + Cloudflare Tunnel
│   ├── docker-compose.mysql.yml     # Shared MySQL (one DB server for the VM)
│   └── DEPLOY.md                    # Deploy runbook
├── jenkins/
│   ├── Dockerfile.agent             # Jenkins build agent
│   ├── Jenkinsfile.cd               # Continuous Deployment pipeline
│   └── Jenkinsfile.ci.cd            # CI/CD pipeline
├── script/
│   ├── run_dev.sh                   # Dev startup: install deps, mypy, migrate, run Flask
│   └── create_migration.sh          # Alembic autogenerate migration shortcut
└── src/
    ├── app.py                       # Main Flask app: routes, teardown, static serving
    ├── app_config.py                # App factory, logger, DB init, session creation
    ├── api/                         # API route modules (Flask Blueprints)
    │   ├── __init__.py              # Exports all Blueprint instances
    │   ├── auth.py                  # Sign-up, log-in endpoints
    │   ├── route.py                 # CRUD + Excel for routes (Precios)
    │   ├── product.py               # CRUD + Excel for products
    │   ├── driver.py                # CRUD + Excel for drivers (Nomina)
    │   ├── shipment.py              # CRUD + Excel for shipments (Cobranzas)
    │   ├── shipment_payroll.py      # Shipment payroll management + Excel
    │   ├── shipment_expense.py      # Shipment expense management + Excel
    │   ├── driver_payroll.py        # Driver payroll management + Excel
    │   ├── dinatran.py              # Dinatran regulatory report generation
    │   ├── statistics.py            # Statistics/analytics endpoints + Excel
    │   └── user_profile.py          # User profile management
    ├── decorators/
    │   └── token_required.py        # JWT auth decorator
    ├── models/                      # SQLAlchemy ORM models
    │   ├── __init__.py              # Re-exports all models
    │   ├── base.py                  # DeclarativeBase
    │   ├── user.py                  # User model (UUID PK)
    │   ├── route.py                 # Route + RouteAudit
    │   ├── product.py               # Product + ProductAudit
    │   ├── driver.py                # Driver + DriverAudit
    │   ├── shipment.py              # Shipment + ShipmentAudit
    │   ├── shipment_payroll.py      # ShipmentPayroll + ShipmentPayrollAudit
    │   ├── shipment_expense.py      # ShipmentExpense + ShipmentExpenseAudit
    │   ├── driver_payroll.py        # DriverPayroll + DriverPayrollAudit
    │   └── api_models.py           # GroupedShipments data class for report aggregation
    ├── migrations/
    │   ├── alembic.ini              # Alembic config
    │   ├── env.py                   # Alembic env (loads .env for DB connection)
    │   ├── script.py.mako           # Migration template
    │   ├── versions/                # Applied migrations
    │   └── not-applied/             # Pending migrations (triggers)
    ├── static/
    │   └── planilla_formato.xlsx    # Excel template for payroll reports
    └── utils/
        ├── locale.py                # i18n: Accept-Language header parsing, message lookup
        ├── pdf.py                   # Excel to PDF conversion via LibreOffice
        └── security.py              # Password hashing (PBKDF2), email/password validation
```

## Environment Variables

Create a `.env` file in the project root with:

```
DB_USERNAME=root
DB_PASSWORD=root
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=dyrtransportes
DEBUG=1
API_KEY=your-secret-key
```

- `DEBUG=1` enables CORS headers, verbose logging, and SQLAlchemy query logging
- `API_KEY` is used as the Flask `SECRET_KEY` for JWT signing

## Development Commands

```bash
# Install dependencies
pip install -r requirements-common.txt
pip install -r requirements-dev.txt

# Type checking
mypy src/

# Linting
pylint src/

# Run migrations
alembic -c src/migrations/alembic.ini upgrade head

# Start dev server (port 8080)
flask --app src/app.py run --host 0.0.0.0 --port 8080 --debug

# All-in-one dev script
./script/run_dev.sh

# Create a new migration
./script/create_migration.sh
# (runs: alembic -c src/migrations/alembic.ini revision --autogenerate -m "new_migration")
```

## Architecture & Key Patterns

### Application Initialization (app_config.py)

The app initializes in this order:
1. `create_flask_app()` - Creates Flask instance, sets SECRET_KEY, adds CORS in debug mode
2. `create_flask_logger()` - Configures separate info.log and error.log file handlers with request context
3. `init_database_and_migrate()` - Creates SQLAlchemy engine with connection pooling, runs `Base.metadata.create_all()`, then runs Alembic migrations, returns a `scoped_session`

The globals exported from `app_config`: `app`, `logger`, `db_session`. API modules only import `logger` and `db_session`; they no longer depend on `app` directly.

### Route Registration

Each API module defines a Flask `Blueprint` (e.g., `shipment_bp = Blueprint("shipment", __name__)`). Routes use `@blueprint.route()` decorators. All blueprints are exported from `src/api/__init__.py` and registered on `app` in `src/app.py` via `app.register_blueprint()`.

### API URL Pattern

All API endpoints follow this pattern:
- **Public:** `/api/...` (e.g., `/api/hello-world`, `/api/auth/log-in`)
- **Protected:** `/api/protected/...` (requires JWT via `@token_required` decorator)
- **Excel exports:** `/api/protected/.../excel` (returns `.xlsx` files)

### Authentication

- JWT tokens via `PyJWT` with HS256 algorithm
- `@token_required` decorator in `src/decorators/token_required.py`
- Token sent in `Authorization: Bearer <token>` header
- Decoded user is attached to `request.current_user` (typed as `RequestWithUser`)
- Token expiry: 1 day default, 7 days with "remember me"

### Database & Models

- All models inherit from `Base` (SQLAlchemy `DeclarativeBase`)
- Models use SQLAlchemy 2.0 `Mapped`/`mapped_column` style with `@dataclass` decorator for serialization
- Every entity has a corresponding `*Audit` table for change tracking
- Common fields on all models: `deleted` (soft delete flag), `modification_user`, `modification_timestamp`
- Soft deletes: Records are never physically deleted; `deleted` is set to `True`
- Decimal fields use `Numeric(10, 2)` for monetary values
- Models include `@validates` decorators for input validation

### Entity Relationships

```
User (auth only, UUID PK)

Driver (driver_code PK) ──┬── DriverPayroll (payroll_code PK)
                          └── Shipment (shipment_code PK)
                                  ├── Route (route_code PK)
                                  ├── Product (product_code PK)
                                  ├── ShipmentPayroll (payroll_code PK)
                                  ├── DriverPayroll (payroll_code PK)
                                  └── ShipmentExpense (expense_code PK)
```

### Internationalization (i18n)

- Each API module defines a `MESSAGES` dict with `"en"` and `"es"` translations
- `get_locale()` reads the `Accept-Language` header; defaults to `"en"`, returns `"es"` if Spanish
- `get_message(MESSAGES, key)` looks up the translated string
- All user-facing messages (errors, success) go through this system

### Excel Export Pattern

Most CRUD modules include an Excel export endpoint. The pattern is:
1. Query data from DB
2. Create `openpyxl.Workbook`
3. Write headers and data rows with styling (borders, number formats)
4. Return via `make_response()` with `Content-Disposition: attachment` and MIME type `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

### PDF Export Pattern

PDF exports (`/api/.../export-pdf`) are the Excel export converted, the same as
choosing "print as PDF" in Excel. There is no second layout to maintain:
1. The workbook building lives in a `build_*_workbook()` function returning the
   `Workbook`, shared by the Excel and the PDF endpoint
2. The builder ends with `set_print_page_setup()` (landscape, fit to width,
   repeated header rows), the page setup a user would set before printing
3. The PDF endpoint calls `excel_to_pdf(workbook, get_locale())` from
   `utils/pdf.py`, which runs LibreOffice headless; LibreOffice calculates the
   formulas left in the cells and formats numbers with the client's locale
4. Return via `make_response()` with `Content-Disposition: attachment` and MIME
   type `application/pdf`

LibreOffice (`libreoffice-calc-nogui`) must be installed in the image; the
binary can be overridden with the `SOFFICE_PATH` environment variable.

### CRUD Endpoint Pattern

Each API module follows a consistent pattern:
1. **GET list** - Query with optional filters (query params), return JSON array
2. **GET by ID** - Single record lookup
3. **POST** - Create new record, set `modification_user` from `request.current_user`
4. **PUT/PATCH** - Update record, create audit entry before modifying
5. **DELETE** - Soft delete (sets `deleted = True`)
6. **GET excel** - Export data as `.xlsx`

Error handling pattern:
- Wrap DB operations in try/except for `SQLAlchemyError`, `OperationalError`, `IntegrityError`
- Call `db_session.rollback()` on failure
- Return localized error message with appropriate HTTP status code
- Log errors via `logger.error()`

### Request Type Annotation

A common pattern across API files is the `request: RequestWithUser` type re-annotation at module level. This provides type hints for `request.current_user` after the `@token_required` decorator sets it.

## Code Conventions

- **Blueprints** - Each API module defines a Blueprint; routes use `@blueprint.route()`. Blueprints are registered in `app.py`. API modules import `logger` and `db_session` from `app_config` but never `app` directly. Use `current_app` when accessing app config (e.g., `current_app.config["SECRET_KEY"]`).
- **Explicit imports** - `src/api/__init__.py` exports named Blueprint instances; `src/models/__init__.py` exports model classes
- **Form data** - POST/PUT endpoints read `request.form` (not JSON body) for most data
- **Audit trail** - Before any update, the current state is copied to the `*_audit` table
- **Soft deletes** - Use `deleted` boolean field; never use SQL DELETE
- **Spanish domain terms** - Cobranzas (shipments/collections), Nomina (payroll), Precios (routes/prices), Liquidacion (settlements)
- **modification_user** - Always set to `request.current_user.name` on create/update operations

## Docker

```bash
# Build production image
docker build -t dyrtransportes-flask:1.10.0 -f docker/Dockerfile .

# Run with docker-compose (includes MySQL + Adminer)
docker-compose -f deploy/docker-compose.prod.yml up -d
```

The production container runs uWSGI on port 8080. The compose stack includes:
- `dyrtransportes-flask` - The API server
- `dyrtransportes-mysql` - MySQL 9.2.0 database
- `dyrtransportes-adminer` - Adminer DB admin UI

## Testing

The suite runs with pytest and lives in `tests/`:

```
tests/
├── conftest.py            # test database, app, client, auth and data factories
├── helpers.py             # helpers shared by the tests, never import from conftest
├── unit/                  # utils and model validators, no database
├── integration/           # the API against a real MySQL: CRUD, auth, scoping
└── functional/            # exports, PDF conversion, formula injection, migrations
```

```bash
# Test database (data only lives in the container)
docker compose -f deploy/docker-compose.test.yml up -d

pytest                       # everything
pytest tests/unit            # no database needed
pytest -m "not pdf"          # skip what needs LibreOffice
pytest --cov=src             # with coverage

./script/run_tests.sh        # database + dependencies + pytest
```

Conventions:
- Tests that touch the database are marked `@pytest.mark.db` and **skip
  themselves** when MySQL is unreachable; those needing LibreOffice are marked
  `@pytest.mark.pdf`
- `conftest.py` sets the DB_* variables before importing the app, which builds
  its engine at import time. The database is `dyrtransportes_test`, never the
  development one, and every table is truncated between tests
- Records are created through the API with the `api` factory fixture, so the
  tests exercise the endpoints instead of writing rows behind their back
- Static checks stay the same: `mypy src/` and `pylint src/`

---

## Workflow Orchestration

### 1. Plan Mode Default

Before making any non-trivial change, enter plan mode first. Read the relevant files, understand the existing patterns (CRUD structure, audit trail, i18n messages), then outline the approach before writing code.

### 2. Subagent Strategy

Use subagents for parallelizable research tasks:
- Exploring multiple API modules simultaneously
- Searching for usage patterns across the codebase (e.g., how `db_session` is used, how audit entries are created)
- Investigating model relationships and foreign key dependencies

Avoid subagents for simple, single-file edits.

### 3. Self-Improvement Loop

After completing a change:
1. Run `mypy src/` to verify type correctness
2. Run `pylint src/` to check code quality
3. If errors are found, fix them before considering the task done
4. Re-run checks until clean

### 4. Verification Before Done

Never mark a task as complete without verifying:
- `mypy src/` passes without new errors
- New API endpoints follow the existing CRUD pattern (MESSAGES dict, `@token_required`, try/except with rollback)
- New models include `*Audit` companion table, `deleted`/`modification_user`/`modification_timestamp` fields
- Both `"en"` and `"es"` translations are provided for all new user-facing messages
- New API modules are re-exported in `src/api/__init__.py`
- New models are re-exported in `src/models/__init__.py`

### 5. Demand Elegance (Balanced)

Write code that matches the existing style:
- Follow the established patterns exactly (don't introduce new frameworks, abstractions, or paradigms)
- Keep endpoint handlers self-contained within their API module
- Use `Decimal` for all monetary values, never `float`
- Use `@validates` decorators on model fields where appropriate
- Keep Excel export logic within the same API module as the CRUD endpoints

Avoid over-engineering: don't add Blueprints, abstract base classes, or service layers unless explicitly requested.

### 6. Autonomous Bug Fixing

When encountering errors during development:
- Read the full traceback and identify the root cause
- Check if the issue is a pattern mismatch (e.g., missing import in `__init__.py`, wrong column type)
- Fix the issue and re-run verification (`mypy src/`)
- Do not ask the user unless the fix requires a design decision

## Task Management

1. **Plan First** - Read all relevant files before making changes. Understand the existing endpoint patterns in the target API module and related model definitions.
2. **Verify Plan** - Confirm the approach matches existing conventions (route naming, error handling, audit trail creation, i18n).
3. **Track Progress** - Use the todo list for multi-step tasks. Mark each step complete as it finishes.
4. **Explain Changes** - Briefly describe what was changed and why when presenting results.
5. **Document Results** - After completing a task, summarize: files modified, endpoints added/changed, migrations created.
6. **Capture Lessons** - If a new pattern or convention is discovered during work, suggest updating this CLAUDE.md.

## Core Principles

- **Simplicity First** - Match the existing codebase style. This project uses straightforward Flask patterns without complex abstractions. Don't introduce unnecessary complexity.
- **No Laziness** - Never use placeholder code, `# TODO: implement later`, or skip audit table creation. Every model gets an audit table. Every endpoint gets both language translations. Every DB operation gets proper error handling with rollback.
- **Minimal Impact** - Make the smallest change that achieves the goal. Don't refactor surrounding code, rename existing variables, add type hints to untouched code, or reorganize imports in files you didn't modify.
