"""
Seed a synthetic demo dataset for the D y R Transportes demo — via the public API,
so validation, hashing and audit triggers all run normally. All data is obviously
fake. Idempotent: if the demo account already has shipments, it exits without
duplicating.

Run once after the stack is up:
    docker compose --env-file .env -f docker-compose.yml run --rm seed
"""

import os
import sys
from datetime import datetime, timedelta

import requests

BASE = os.environ.get("API_BASE", "http://dyrtransportes-flask:8080")
EMAIL = os.environ.get("DEMO_EMAIL", "demo@rad710.com")
# Must satisfy the API rule: >=8 chars, 1 upper, 1 lower, 1 digit.
PASSWORD = os.environ.get("DEMO_PASSWORD", "DemoPass123")

s = requests.Session()


def rows(resp):
    """Normalize a list response — the API may wrap it or return a bare list."""
    try:
        body = resp.json()
    except Exception:
        return []
    if isinstance(body, list):
        return body
    if isinstance(body, dict):
        for key in ("data", "result", "results", "items"):
            if isinstance(body.get(key), list):
                return body[key]
    return []


def die(msg, resp=None):
    print(f"[seed] ERROR: {msg}")
    if resp is not None:
        print(f"       {resp.status_code} {resp.text[:300]}")
    sys.exit(1)


# --- 1. demo account (idempotent) -------------------------------------------
r = s.post(f"{BASE}/api/auth/sign-up", data={"name": "Demo", "email": EMAIL, "password": PASSWORD})
if r.status_code in (200, 201):
    print(f"[seed] created demo account {EMAIL}")
elif r.status_code == 409:
    print(f"[seed] demo account {EMAIL} already exists")
else:
    die("sign-up failed", r)

r = s.post(f"{BASE}/api/auth/log-in", data={"email": EMAIL, "password": PASSWORD})
if r.status_code != 200:
    die("log-in failed", r)
token = r.json().get("token")
if not token:
    die("no token in log-in response", r)
s.headers.update({"Authorization": f"Bearer {token}"})
print("[seed] logged in")

# --- idempotency: bail if already populated ---------------------------------
existing = rows(s.get(f"{BASE}/api/shipments"))
if existing:
    print(f"[seed] {len(existing)} shipments already present — nothing to do.")
    sys.exit(0)


def create(path, payload, label):
    r = s.post(f"{BASE}{path}", json=payload)
    if r.status_code not in (200, 201):
        print(f"[seed] WARN creating {label}: {r.status_code} {r.text[:160]}")
    return r


def code_map(list_path, key_field, code_field):
    """Map a natural key -> generated code by reading the list back."""
    return {row[key_field]: row[code_field] for row in rows(s.get(f"{BASE}{list_path}")) if key_field in row}


# --- 2. reference data ------------------------------------------------------
PRODUCTS = ["Soja", "Maíz", "Trigo", "Girasol"]
for name in PRODUCTS:
    create("/api/product", {"product_name": name}, f"product {name}")
product_code = code_map("/api/products", "product_name", "product_code")
print(f"[seed] products: {product_code}")

ROUTES = [
    # origin, destination, price, payroll_price  (Guaraníes per trip)
    ("Katueté", "Villeta", 4200000, 3600000),
    ("Campo 9", "Asunción", 3800000, 3200000),
    ("Naranjal", "Encarnación", 2600000, 2200000),
    ("Santa Rita", "Villeta", 4500000, 3900000),
    ("Bella Vista", "Ciudad del Este", 1800000, 1500000),
]
for origin, dest, price, payroll_price in ROUTES:
    create(
        "/api/route",
        {"origin": origin, "destination": dest, "price": price, "payroll_price": payroll_price},
        f"route {origin}->{dest}",
    )
route_rows = rows(s.get(f"{BASE}/api/routes"))
route_by_pair = {(r["origin"], r["destination"]): r for r in route_rows if "origin" in r}
print(f"[seed] routes: {len(route_rows)}")

DRIVERS = [
    # driver_id, name, surname, truck_plate, trailer_plate
    ("3921544", "Juan", "Giménez", "ABC123", "TRL010"),
    ("4185220", "María", "Benítez", "DEF456", "TRL011"),
    ("2874109", "Carlos", "Rojas", "GHI789", "TRL012"),
    ("5102873", "Ana", "Villalba", "JKL321", "TRL013"),
]
for did, name, surname, truck, trailer in DRIVERS:
    create(
        "/api/driver",
        {
            "driver_id": did,
            "driver_name": name,
            "driver_surname": surname,
            "truck_plate": truck,
            "trailer_plate": trailer,
        },
        f"driver {name}",
    )
driver_rows = rows(s.get(f"{BASE}/api/drivers"))
print(f"[seed] drivers: {len(driver_rows)}")

# --- 3. payrolls ------------------------------------------------------------
now = datetime(2026, 8, 1, 8, 0, 0)  # fixed base date for reproducibility


def ts(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


create("/api/shipment-payroll", {"payroll_timestamp": ts(now)}, "shipment payroll")
sp_rows = rows(s.get(f"{BASE}/api/shipment-payrolls"))
shipment_payroll_code = sp_rows[0]["payroll_code"] if sp_rows else None

driver_payroll_code = {}
for d in driver_rows:
    dc = d["driver_code"]
    create("/api/driver-payroll", {"driver_code": dc, "payroll_timestamp": ts(now)}, f"driver payroll {dc}")
for d in driver_rows:
    dc = d["driver_code"]
    dp = rows(s.get(f"{BASE}/api/driver/{dc}/payrolls"))
    if dp:
        driver_payroll_code[dc] = dp[0]["payroll_code"]

if not (shipment_payroll_code and driver_payroll_code):
    die("could not resolve payroll codes — check the payroll endpoints/response shape")

# --- 4. shipments -----------------------------------------------------------
count = 0
for i in range(28):
    d = driver_rows[i % len(driver_rows)]
    (origin, dest, price, payroll_price) = ROUTES[i % len(ROUTES)]
    route = route_by_pair.get((origin, dest))
    pname = PRODUCTS[i % len(PRODUCTS)]
    if not route:
        continue
    origin_w = 30000 + (i % 6) * 2000
    dest_w = origin_w - (i % 3) * 150  # small transit loss
    shipment_date = now - timedelta(days=42 - i, hours=(i % 5))
    r = create(
        "/api/shipment",
        {
            "shipment_date": ts(shipment_date),
            "driver_code": d["driver_code"],
            "driver_name": d["driver_name"],
            "truck_plate": d["truck_plate"],
            "trailer_plate": d.get("trailer_plate"),
            "product_code": product_code.get(pname),
            "product_name": pname,
            "route_code": route["route_code"],
            "origin": origin,
            "destination": dest,
            "price": price,
            "payroll_price": payroll_price,
            "dispatch_code": f"D-{1000 + i}",
            "receipt_code": f"R-{2000 + i}",
            "origin_weight": origin_w,
            "destination_weight": dest_w,
            "shipment_payroll_code": shipment_payroll_code,
            "driver_payroll_code": driver_payroll_code[d["driver_code"]],
        },
        f"shipment {i}",
    )
    if r.status_code in (200, 201):
        count += 1

print(f"[seed] done — {count} shipments created. Demo login: {EMAIL} / {PASSWORD}")
