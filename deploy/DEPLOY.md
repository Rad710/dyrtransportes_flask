# Deploy — D y R Transportes

Deploy configs for this app. Two compose files, named by purpose:

| File | What it is |
| --- | --- |
| `docker-compose.prod.yml` | **Production** — the self-contained stack (Flask + its own MySQL + Adminer). |
| `docker-compose.demo.yml` | **Public demo** — web + api + cloudflared, **pull-only** (GHCR), behind its own Cloudflare Tunnel, `expose:` only (no host ports), using the shared MySQL. Plus a one-shot `seed`. |
| `docker-compose.mysql.yml` | The **shared MySQL** for the whole VM — one DB server used by every app (databases `dyr_ai` for text-to-sql, `dyr_demo` for this app). Replaces per-app MySQL containers to save memory. |

Supporting files: `mysql-init/` (creates the databases + users on first boot), `seed/seed.py` (synthetic
demo data via the API), `env.mysql.example` / `env.demo.example`.

The rest of this runbook covers the **demo** deploy.

## 0. Publish images (CI → GHCR)

`.github/workflows/release.yml` in **dyrtransportes_react** and **dyrtransportes_flask** build and push
`ghcr.io/rad710/dyrtransportes-{react,flask}`. Tag a release in each (`git tag v1.0.0 && git push --tags`),
then make both GHCR packages **public**.

## 1. Shared MySQL

Copy this `deploy/` folder to the VM, then:

```bash
cp env.mysql.example .env.mysql && nano .env.mysql      # set 3 strong passwords
docker compose --env-file .env.mysql -f docker-compose.mysql.yml up -d
```

Creates the `shared-db` network and the `dyr_ai` + `dyr_demo` databases (init runs once, on first volume
creation).

## 2. Cloudflare Tunnel for dyr.rad710.com

Tunnels → Create Tunnel → copy the token → Routes → Add route → hostname **`dyr.rad710.com`** →
Service URL **`http://web:80`**.

## 3. Demo stack

```bash
cp env.demo.example .env.demo && nano .env.demo         # CF token, DYR_DB_PASSWORD (== mysql), JWT_SECRET
docker compose --env-file .env.demo -f docker-compose.demo.yml pull
docker compose --env-file .env.demo -f docker-compose.demo.yml up -d
```

The `api` creates its schema + triggers in `dyr_demo` on first boot (it may restart a couple times until the
shared MySQL is reachable — expected).

## 4. Seed demo data (once)

```bash
docker compose --env-file .env.demo -f docker-compose.demo.yml run --rm seed
```

Loads products, routes, drivers, payrolls, ~28 shipments, and the **`demo@rad710.com / DemoPass123`**
account. Idempotent.

## 5. Verify

```bash
docker compose -f docker-compose.demo.yml ps            # web + api healthy, cloudflared up
curl -sSI https://dyr.rad710.com | head -1              # HTTP/2 200
```

## Notes

- No host ports (`expose:` only) — ufw stays SSH-only.
- `DYR_DB_PASSWORD` in `.env.demo` **must equal** the one in `.env.mysql`.
- To point the portfolio/CV at this demo, switch the DyR link from `rad710.pythonanywhere.com` to
  `https://dyr.rad710.com` and swap in a dashboard screenshot.
