# D y R Transportes — API (backend)

REST API for a logistics platform in **daily production use** by a grain-transport company — trips, cargo,
payrolls, and regulatory reporting. **Flask + SQLAlchemy + MySQL.**

Frontend: **[dyrtransportes_react](https://github.com/Rad710/dyrtransportes_react)**.

🔗 **Live:** [rad710.pythonanywhere.com](https://rad710.pythonanywhere.com/)

## What it does

REST resources for auth, drivers, routes, products, shipments, shipment payrolls, shipment expenses, driver
payrolls, DINATRAN reporting, statistics, and user profiles — plus:

- **JWT auth** via a `@token_required` decorator; hashed passwords; UUID-keyed users.
- **Payrolls & expenses** built from shipment records, with an **audit trail** (soft-delete + modification
  user/timestamp).
- **Excel export** (openpyxl) and amount-to-words (num2words) for receipts.
- **DINATRAN** regulatory transport reporting.
- A token-protected **live `mysqldump` backup** endpoint that streams a timestamped `.sql`.
- Bilingual (ES/EN) error/message dictionaries.

## Stack

Python · **Flask 3.1** · **SQLAlchemy 2.0** (typed `Mapped[]` ORM) · MySQL · **Alembic** migrations · PyJWT ·
openpyxl · num2words. Production server: **uWSGI**. Tooling: mypy.

## Layout

```
src/api/          Flask blueprints — one per resource
src/models/       SQLAlchemy ORM models   (Shipment is the core entity)
src/decorators/   token_required
src/utils/        security (hashing) · locale (i18n messages)
src/migrations/   Alembic
```

RESTful design with proper verbs and resource URLs (e.g. `GET/PUT/PATCH /api/shipment/<code>`,
`POST /api/shipments/change-payroll`). A catch-all route serves the built React SPA for client-side routing.

## Run

```bash
# 1. a MySQL database
docker run -d --name dyr-mysql \
  -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=dyrtransportes \
  -p 3306:3306 mysql:8

# 2. install deps, run migrations, and serve (see script/run_dev.sh)
./script/run_dev.sh          # → http://localhost:8080
```

`.env`:

```env
DB_USERNAME=root
DB_PASSWORD=root
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=dyrtransportes
DEBUG=1
API_KEY=change-me
```

New migration: `./script/create_migration.sh "<message>"`.

## Deploy

Dockerized (non-root uWSGI, slim Python) and self-hosted end-to-end via a **solo-built Jenkins pipeline** —
multi-architecture images, SonarQube gates, automatic GitHub releases, and remote deploy over SSH. In
production, nginx reverse-proxies `/api/` to this service and serves the built frontend.

Frontend: **[dyrtransportes_react](https://github.com/Rad710/dyrtransportes_react)**.
