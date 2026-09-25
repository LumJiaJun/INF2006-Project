# Architecture — StaySphere

## Diagram

```
                              USERS (guests)
                                   |
                                 HTTPS
                                   |
                    ┌──────────────────────────┐
                    │   Frontend (static site)  │   src/frontend/
                    │   HTML + JS, no build step │
                    │   + Leaflet/OSM map        │
                    └──────────────┬─────────────┘
                                   | fetch() JSON over HTTPS
                                   v
   ┌───────────────────────────────────────────────────────────┐
   │              Application Load Balancer (AWS ALB)            │  <- MANUAL: AWS
   │              health check -> GET /api/health                 │
   └──────────────────────────────┬────────────────────────────┘
                                   |
                     ┌─────────────┴─────────────┐
                     v                             v
          ┌────────────────────┐        ┌────────────────────┐
          │ Backend instance 1  │        │ Backend instance 2  │   ECS Fargate task
          │ FastAPI (uvicorn)   │  ...   │ (horizontal scale)  │   or EC2 (trust boundary:
          │ - auth (JWT)        │        │                     │   only ALB reachable from
          │ - listings/search   │        │                     │   internet; backend in
          │ - bookings          │        │                     │   private subnet)
          │ - ml/price-estimate │        │                     │
          └──────────┬──────────┘        └──────────┬──────────┘
                     │                               │
                     └───────────────┬───────────────┘
                                      v
                         ┌─────────────────────────┐
                         │  Amazon RDS PostgreSQL    │   <- MANUAL: AWS
                         │  (users, listings_source, │      private subnet,
                         │   bookings)                │      security group allows
                         └─────────────────────────┘      only backend SG, not 0.0.0.0/0

                         ┌─────────────────────────┐
                         │  ML model artifact        │   analytics/ -> joblib file
                         │  (price_model.joblib)     │   baked into backend image
                         │  trained offline, loaded   │   or pulled from S3 at
                         │  at API startup            │   startup
                         └─────────────────────────┘

                         ┌─────────────────────────┐
                         │  CloudWatch Logs/Metrics  │   <- MANUAL: AWS
                         │  (stdout logs from        │
                         │   uvicorn/FastAPI)         │
                         └─────────────────────────┘
```

Trust boundaries:
- Internet <-> ALB: public, HTTPS only.
- ALB <-> backend: backend runs in a private subnet, not directly internet-reachable.
- Backend <-> RDS: security group only allows the backend's security group on port 5432, never `0.0.0.0/0`.
- No component holds long-lived AWS credentials in code; IAM roles attached to compute resources instead (see `docs/DEPLOYMENT.md`).

## Service model and deployment model

**Chosen:** IaaS-adjacent managed container platform — AWS ECS Fargate (serverless containers) for the backend, S3 static website hosting (or CloudFront + S3) for the frontend, RDS PostgreSQL (managed database, PaaS) for the data layer.

This sits at the **PaaS boundary**: we manage the container image and application code; AWS manages the underlying VM, OS patching, and container orchestration for Fargate, and the database engine/backups/patching for RDS.

## Alternatives considered and why not selected

| Alternative | Considered for | Why not selected |
|---|---|---|
| **EC2 (self-managed VM)** | Backend compute | More control, but requires the team to patch the OS, manage scaling manually, and configure a process manager. Given the 3-week timeline and solo-then-small-team setup, the operational overhead outweighs the benefit for this project's scale. Documented as a valid alternative in `docs/CLOUD_TRADEOFFS.md`. |
| **AWS Elastic Beanstalk** | Backend compute | Simpler than raw EC2, but less transparent about the underlying resources it creates, which makes it harder to produce clear, labelled evidence of what's actually running (a rubric requirement). ECS Fargate gives an explicit task definition and service config to point to as evidence. |
| **DynamoDB** | Data layer | NoSQL fits key-value access patterns well, but this application's data (listings with many filterable columns, relational bookings-to-listings-to-users) is naturally relational, and the search/filter requirement benefits from SQL's `WHERE`/`ORDER BY`/indexing over multiple columns at once. RDS PostgreSQL was chosen instead. |

## Assumptions, constraints, workload

- Academic project, single small team, ~3-week build window.
- Expected workload: light — a handful of concurrent users during grading/demo, not real production traffic. Architecture favours simplicity and cost control over aggressive scaling.
- All data is synthetic or self-generated; no real personal data, no real payments.
- Cost-control measures: smallest available Fargate task size, RDS `db.t3.micro` (or free-tier eligible instance), no NAT gateway (backend can reach the internet only if genuinely needed — currently it doesn't need outbound internet access), resources torn down after grading, AWS Budget alert configured (see `docs/DEPLOYMENT.md`).

## Scalability and resilience mechanism (implemented)

1. **Stateless backend** — JWT auth carries all session state in the token itself, so any backend instance can serve any request. This is what makes horizontal scaling (running 2+ instances behind the ALB) possible without sticky sessions.
2. **Health check endpoint** (`GET /api/health`) — checks DB connectivity, used by the ALB target group and by Docker's `HEALTHCHECK` to detect and route around/restart unhealthy instances.
3. **Connection pooling** — SQLAlchemy engine configured with `pool_pre_ping`, bounded `pool_size`/`max_overflow` so the app doesn't exhaust DB connections under load.
4. **In-process TTL cache** on the analytics endpoint — reduces repeated aggregate-query load on the DB, standing in for what a Redis/ElastiCache layer would do at larger scale.

See `tests/04_scalability_resilience/` for the automated tests and `evidence/test-resilience.md` for results.

## External dependencies (non-AWS)

The map view loads Leaflet's JS/CSS from cdnjs and map tiles from the
public OpenStreetMap tile server, both over HTTPS from the browser
directly — no backend involvement, no API key required, no cost to us.
If this ever needed to scale beyond light academic/demo traffic, OSM's
usage policy would require switching to a paid tile provider (e.g.
MapTiler, Mapbox) — noted here rather than treated as production-ready
as-is.

## Observability

- Structured request logging (method, path, status, duration) to stdout on every request — picked up by CloudWatch Logs when deployed via ECS's `awslogs` driver.
- Application-level logs for auth events (registration, login success/failure) and booking events (created, cancelled).
- `GET /api/health` doubles as the operational monitoring endpoint referenced in `evidence/monitoring.md`.
