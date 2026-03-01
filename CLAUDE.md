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
│   ├── Dockerfile                   # Production image (python:3.13-slim-bookworm)
│   └── docker-compose.yaml          # Flask + MySQL + Adminer stack
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
    ├── api/                         # API route modules (registered via wildcard imports)
    │   ├── __init__.py              # Re-exports all API modules
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

The three globals exported from `app_config` and used everywhere: `app`, `logger`, `db_session`.

### Route Registration

Routes are registered directly on the `app` object (no Blueprints yet - this is a known TODO). All API modules in `src/api/` use `@app.route()` decorators and are imported via wildcard in `src/api/__init__.py`, which is then imported from `src/app.py`.

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

- **No Blueprints** - Routes are registered directly on `app`. A TODO exists to add Blueprint organization.
- **Wildcard imports** - `src/api/__init__.py` and `src/models/__init__.py` use `from .module import *`
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
docker-compose -f docker/docker-compose.yaml up -d
```

The production container runs uWSGI on port 8080. The compose stack includes:
- `dyrtransportes-flask` - The API server
- `dyrtransportes-mysql` - MySQL 9.2.0 database
- `dyrtransportes-adminer` - Adminer DB admin UI

## Testing

There is no test suite currently. Use `mypy` for static type checking and `pylint` for linting:

```bash
mypy src/
pylint src/
```

## Important Notes for AI Assistants

- The `src/` directory is the Python source root. Imports use module names relative to `src/` (e.g., `from app_config import app`, `from models.user import User`).
- Do not add Blueprints without explicit instruction - there is a TODO for this but it's a significant refactor.
- All monetary values must use `Decimal` (never `float`).
- Always include both `"en"` and `"es"` translations when adding new user-facing messages.
- When adding new models, follow the existing pattern: `@dataclass`, `Mapped`/`mapped_column`, `*Audit` companion table, `deleted`/`modification_user`/`modification_timestamp` fields.
- When adding new API endpoints, follow the existing pattern: define `MESSAGES` dict, use `@token_required`, handle errors with try/except + rollback, return localized messages.
- The `db_session` is a `scoped_session` and is cleaned up in `app.teardown_appcontext`.
- Static files in `src/static/` serve the React frontend build. The catch-all route in `app.py` serves `index.html` for client-side routing.
