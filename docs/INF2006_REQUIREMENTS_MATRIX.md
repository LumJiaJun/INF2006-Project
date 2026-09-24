# INF2006 Requirements Matrix — StaySphere

Honest status against the brief's Section 4 minimum requirements and
Section 5 design/evaluation requirements. PASS = implemented and
tested. PARTIAL = implemented but not fully tested/deployed. MANUAL
USER ACTION REQUIRED = depends on the team's AWS account.

| Requirement (brief §4/5) | Implementation | File/path | Evidence | Status |
|---|---|---|---|---|
| Working web app/API, one meaningful workflow, input validation | Guest workflow: register→login→search→view→book→cancel→my trips; Pydantic validation on every request | `src/backend/app/`, `src/frontend/` | `evidence/test-functional.md` | PASS |
| Cloud deployment (VM/PaaS/container), explained IaaS/PaaS/SaaS boundary | Dockerized app, targeting ECS Fargate; boundary explained | `src/backend/Dockerfile`, `docker-compose.yml`, `docs/ARCHITECTURE.md` | `docs/ARCHITECTURE.md` (service model section) | PARTIAL — containerized and documented, not yet deployed to AWS |
| Persistent cloud DB with defined schema, no production creds/personal data | PostgreSQL schema (SQLAlchemy models), synthetic data only | `src/backend/app/models.py`, `docs/DATABASE_SCHEMA.md` | `docs/DATABASE_SCHEMA.md` | PASS (schema + local Postgres via Docker Compose); RDS itself is MANUAL USER ACTION REQUIRED |
| One interpretable analytics/AI feature | Price estimator (Linear Regression vs Random Forest, real MAE/RMSE/R²), applied both directly (`/api/ml/price-estimate`) and inside a budget-based recommendation ranking (`/api/recommendations`) that flags below-model-estimate listings as "great value" | `analytics/train_price_model.py`, `src/backend/app/routers/ml.py`, `routers/recommendations.py`, `pricing.py` | `evidence/test-data-ai.md` | PASS (on synthetic data — real dataset pending) |
| Scalability/resilience mechanism, documented and tested | Health check, stateless JWT auth, connection pooling, TTL cache | `src/backend/app/routers/health.py`, `listings.py`, `database.py` | `evidence/test-resilience.md` | PASS (local mechanism + tests); real container-restart recovery test is NOT YET EXECUTED |
| Auth/authz, least privilege, secrets, network restriction, named threat tested | JWT + bcrypt + role-based access control (guest vs admin, enforced on `/api/admin/*`) + object-level auth; 8 named threats mapped | `src/backend/app/auth.py`, `routers/admin.py`, `docs/THREAT_MODEL.md` | `evidence/threat-control-map.md`, `evidence/test-security.md` | PASS (app-level); AWS network-level control (RDS security group) is MANUAL USER ACTION REQUIRED |
| Logging/monitoring + one operational test/query | Structured request/auth/booking logging | `src/backend/app/main.py` | `evidence/monitoring.md` | PARTIAL — local logging implemented and sampled; CloudWatch integration NOT YET EXECUTED (no deployment yet) |
| Architecture diagram with trust boundaries, data flows | Diagram generated and included | `evidence/architecture.png` | `docs/ARCHITECTURE.md` | PASS |
| Interactive map (brief §37, if lat/long present) | Leaflet + OpenStreetMap map of current search results, clickable markers; plus an admin geographic demand/price heatmap (circle markers by city, sized by listing count, coloured by relative price) | `src/frontend/index.html`, `app.js`, `src/backend/app/routers/admin.py` (`/pricing-insights`) | manual browser check | PASS (client-side; no automated test — Leaflet/OSM reachability can't be verified from this sandboxed build environment, only from a real browser) |
| Admin operational visibility into guest bookings | `/api/admin/bookings` + dashboard table, proven to reflect a real guest booking | `src/backend/app/routers/admin.py` | `evidence/test-data-ai.md` (`test_booking_made_by_guest_is_visible_to_admin`) | PASS |
| ≥2 alternatives considered per major choice, with rationale | Compute and data-layer alternatives compared | `docs/CLOUD_TRADEOFFS.md` | `docs/CLOUD_TRADEOFFS.md` | PASS |
| 4 required tests (functional, security, data/AI, scalability/resilience) | All 4 automated, all passing locally | `tests/` | `evidence/test-*.md`, `evidence/pytest-output.txt` | PASS (locally); deployment-dependent sub-checks NOT YET EXECUTED |
| Submission package structure | README, manifest, src, data, analytics, evidence, tests, declarations all present | repo root | this file | PASS |
| project_manifest.yaml matches required schema | All required fields present, no renames | `project_manifest.yaml` | validated with `python3 -c "import yaml; yaml.safe_load(open('project_manifest.yaml'))"` | PASS |
| report.pdf, 8–12 pages, required headings | Not yet written | — | — | NOT YET EXECUTED — write after evidence/deployment is finalized, using the 8 required headings in the brief §7 |
| TEAM_CONTRIBUTIONS.md | Template created, needs real team member rows | `TEAM_CONTRIBUTIONS.md` | — | PARTIAL — placeholder until team is finalized |
| AI_USE_DECLARATION.md | Written, honest about AI's role and what still needs team verification | `AI_USE_DECLARATION.md` | — | PASS |
| No credentials/personal data/tokens in submission | `.env` git-ignored, `.env.example` placeholder-only, all data synthetic | `.gitignore`, `.env.example` | — | PASS |

## Deliberately out of scope for this build (documented, not hidden)

- Host dashboard, review submission workflow
- Clustering/market segmentation, full 20-chart analytics suite
- Real Kaggle dataset (synthetic data used instead, pending download —
  `data/inspect_dataset.py` is ready to run the moment it's downloaded)
- Actual AWS deployment (no AWS account existed at time of this build)

Admin analytics + listing management, the search-results map, the
admin geographic price/demand heatmap (circle markers on a real map,
sized by listing count and coloured by relative price), and the
budget-based recommendation engine were all added as in-scope features.
