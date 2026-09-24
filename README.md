# StaySphere

**A secure, scalable, data-driven cloud accommodation platform**
(INF2006 Cloud Computing & Big Data team project, SIT)

## Problem statement

Build a working, cloud-deployable accommodation booking platform that
demonstrates a real web application/API, a persistent cloud data layer,
one interpretable data-driven AI feature, and the security/scalability/
observability practices expected of a professionally-run cloud service —
all as an academic simulation, not a real commercial product.

## Users

- **Guest** — registers, searches/filters listings, views details, makes
  a simulated booking, views/cancels bookings in My Trips.
- **Admin** — logs in with an admin-role account, sees platform-wide
  analytics (listings, users, bookings, simulated revenue) and can add,
  edit (price) and remove listings from the Admin Dashboard.
- (Host role is modeled in the schema for future extension but is not
  part of this build's core workflow — see `docs/INF2006_REQUIREMENTS_MATRIX.md`.)

## Demo accounts

Created automatically by `python -m app.seed`:

| Role | Email | Password |
|---|---|---|
| Guest | `guest@staysphere.demo` | `Demo1234!` |
| Admin | `admin@staysphere.demo` | `Demo1234!` |

The login page also has one-click "Guest demo" / "Admin demo" buttons
that fill these in automatically.

## Features (current scope)

- Registration / login (JWT auth, bcrypt password hashing)
- Listing search with live-updating filters (city, room type, guest
  count, price range), sorting, an interactive map of the current
  results (Leaflet + OpenStreetMap), and a "Browse by city" popup
- An inline AI price-estimate banner on the search page itself: once
  city + room type (+ optional guest count) are set, the same trained
  model shown elsewhere estimates a fair nightly price for that search
- Listing detail view with full review score breakdown, an availability
  calendar showing already-booked dates, and guest reviews
- Simulated booking with date validation, double-booking prevention
  (both server-enforced and visible on the calendar before you try),
  and a cosmetic simulated-payment step (card fields are never sent to
  the server or stored — no real payment processing, per the academic scope)
- My Trips (view/cancel own bookings, leave a review once a stay has ended)
- "Find your match" recommendation engine: guest enters a budget, guest
  count and optional city, gets ranked listings with a "Great value"
  flag on ones priced below the trained model's fair-price estimate
- **Ask StaySphere** chatbot tab: a rule-based conversational interface
  (keyword/slot extraction, not an external LLM) that asks for missing
  details, re-ranks live as you change your mind ("actually make it
  $100"), and calls the exact same recommendation engine as the "Find
  your match" page and the search banner — one evaluated AI feature,
  three entry points
- Host Price Estimator (the underlying ML endpoint, exposed directly for
  a host sanity-checking a single price — same model as everywhere else)
- Guest reviews: submit a rating + comment for a completed stay,
  duplicate-review prevention, shown publicly on the listing page
- Admin Dashboard: platform-wide analytics, per-city AND per-neighbourhood
  demand/pricing map with a real geographic heatmap (click a location to
  see and edit every room there), a "suggested price" gap per listing
  from the trained model, full listing editing (every meaningful field,
  not just price), a per-listing booking calendar, a live view of every
  booking guests have made, review moderation, and full user management
  (view, change role, delete) — all protected by role-based authorization
- Health check + basic analytics endpoint with caching
- Structured request/event logging

## Architecture

See `docs/ARCHITECTURE.md` for the full diagram and rationale. In short:
static frontend → ALB → containerized FastAPI backend (horizontally
scalable, stateless) → RDS PostgreSQL, with the ML model trained offline
and loaded by the API.

## Technology stack

- **Frontend:** plain HTML/JS + Tailwind (CDN) + Leaflet/OpenStreetMap for the map, no build step
- **Backend:** Python, FastAPI, SQLAlchemy
- **Database:** PostgreSQL (SQLite for local dev)
- **ML:** scikit-learn (Linear Regression, Random Forest), pandas, joblib
- **Auth:** JWT (python-jose), bcrypt (passlib)
- **Containerization:** Docker, Docker Compose
- **Cloud target:** AWS (ECS Fargate, RDS, S3, CloudWatch — see `docs/DEPLOYMENT.md`)

## Dataset

Airbnb Listings and Reviews
(https://www.kaggle.com/datasets/toufikbhm/airbnb-listings-and-reviews).
**Not yet downloaded** — `data/sample/*.csv` currently contains synthetic
data matching the documented schema. See `data/README.md` and
`data/DATA_DICTIONARY.md`.

## Local development

```
git clone <your-repo-url>
cd staysphere
cp .env.example .env
docker compose up -d
docker compose exec backend python -m app.seed
```

Frontend: http://localhost:8080
API docs: http://localhost:8000/docs
Health check: http://localhost:8000/api/health

To run without Docker (backend only, SQLite):

```
cd src/backend
pip install -r requirements.txt
python3 -m app.seed
uvicorn app.main:app --reload
```

## Environment variables

See `.env.example`. `JWT_SECRET` and `DATABASE_URL` are the two that
matter locally; the AWS-related ones are only needed once deployed.

## Database setup / dataset ingestion

`python -m app.seed [csv_path]` loads listing data into the
`listings_source` table. Defaults to `data/sample/dummy_listings.csv`.
Delete `staysphere.db` (SQLite) or the Postgres volume to reseed from
scratch — the script refuses to double-seed a non-empty table.

## Analytics / ML training

```
cd analytics
pip install -r requirements.txt
python3 train_price_model.py
```

See `analytics/README.md` for method details and `evidence/test-data-ai.md`
for the last run's actual metrics.

## Tests

```
cd tests
pip install -r ../src/backend/requirements.txt
pytest -v
```

Four required test categories, each with automated pytest coverage and
a corresponding write-up in `evidence/`:

| # | Category | Automated tests | Evidence |
|---|---|---|---|
| 1 | Functional | `tests/01_functional/` | `evidence/test-functional.md` |
| 2 | Security | `tests/02_security/` | `evidence/test-security.md` |
| 3 | Data/AI | `tests/03_data_ai/` | `evidence/test-data-ai.md` |
| 4 | Scalability/Resilience | `tests/04_scalability_resilience/` | `evidence/test-resilience.md` |

As of 2026-09-21, all 19 automated tests pass locally. Deployment-dependent
checks (real container restart, real AWS security-group verification) are
marked NOT YET EXECUTED until an AWS environment exists — see the evidence
files for exactly which parts.

## Docker

```
docker compose up -d      # start everything
docker compose down       # stop everything
docker compose down -v    # stop and wipe the database volume
```

## AWS deployment

See `docs/DEPLOYMENT.md` — every step is explicitly labeled AUTOMATED or
MANUAL USER ACTION REQUIRED, since AWS account creation and billing must
be done by the project owner.

## Security

JWT auth, bcrypt password hashing, parameterized queries (SQL injection
safe), object-level authorization on bookings, input validation via
Pydantic, secrets via environment variables (never hardcoded). Full
threat model in `docs/THREAT_MODEL.md`.

## Scalability

Stateless backend, health-check-driven load balancing, connection
pooling, TTL-cached analytics endpoint. Details and test evidence in
`docs/ARCHITECTURE.md` and `evidence/test-resilience.md`.

## Monitoring

Structured stdout logging (request, auth, booking events) intended for
CloudWatch Logs once deployed. See `evidence/monitoring.md`.

## Limitations

- Real Kaggle dataset not yet downloaded; current data and ML metrics
  are based on synthetic data matching the documented schema.
- Host/Admin dashboards, review submission, and clustering-based market
  segmentation are out of scope for this build (deliberately, to keep
  the core guest workflow solid rather than spreading effort thin —
  see `docs/INF2006_REQUIREMENTS_MATRIX.md`).
- No rate limiting on login yet (documented in `docs/THREAT_MODEL.md`).
- Not yet deployed to AWS (no account existed at time of writing) — see `docs/DEPLOYMENT.md`.

## Academic disclaimer

This is an academic simulation for INF2006 at SIT. It does not connect
to real Airbnb accounts, does not make real reservations, and does not
process real payments. All data is synthetic or self-generated. "Airbnb"
is referenced only to describe the dataset's origin and is not
affiliated with or endorsed by Airbnb, Inc.

## Open-source references

- FastAPI, SQLAlchemy, Pydantic, scikit-learn, pandas, Tailwind CSS
  (via CDN) — all used under their respective open-source licences
  (MIT/BSD-family). No third-party code was copied verbatim beyond
  standard library usage patterns; see `AI_USE_DECLARATION.md` for how
  AI assistance was used in building this.

## AI-assisted development

See `AI_USE_DECLARATION.md`.
