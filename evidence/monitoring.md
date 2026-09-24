# Monitoring — StaySphere

## What is monitored

- **Every HTTP request:** method, path, response status code, duration
  in ms (logged by the `log_requests` middleware in `app/main.py`).
- **Authentication events:** successful registration, successful login,
  failed login attempts (logged with user ID / email, never password).
- **Booking events:** booking created, booking cancelled (logged with
  booking ID, listing ID, guest ID).
- **Service health:** `GET /api/health` reports overall status and
  database connectivity, polled by Docker's `HEALTHCHECK` locally and
  intended for an ALB target group health check in AWS deployment.
- **Database errors:** the health check logs an error if the `SELECT 1`
  connectivity probe fails.

## Where logs are stored

- **Local/Docker:** stdout, visible via `docker compose logs backend` or
  `docker logs <container>`.
- **AWS (once deployed):** CloudWatch Logs, via the `awslogs` log driver
  configured on the ECS task definition (see `docs/DEPLOYMENT.md` Step 8).
  **NOT YET EXECUTED** — no AWS deployment exists yet to capture a real
  CloudWatch screenshot from.

## Sample log output (captured locally, 2026-09-21)

```
2026-09-21 09:45:28,114 level=INFO logger=staysphere request method=GET path=/api/health status=200 duration_ms=2.4
2026-09-21 09:47:27,658 level=INFO logger=staysphere.auth user_registered user_id=1
2026-09-21 09:47:27,960 level=INFO logger=staysphere.auth login_success user_id=1
2026-09-21 09:47:27,989 level=INFO logger=staysphere.bookings booking_created booking_id=1 listing_id=1 guest_id=1
```

## Sample query (once in CloudWatch Logs Insights)

```
fields @timestamp, @message
| filter @message like /status=5/
| sort @timestamp desc
| limit 20
```
This finds recent 5xx server errors — useful for spotting a backend
failure or a bad deployment quickly. **NOT YET EXECUTED** against real
CloudWatch data.

## Example alert (to configure once deployed)

CloudWatch Alarm on the ALB target group's `HealthyHostCount` metric:
alert if it drops to 0 for 2 consecutive periods, meaning no backend
instance is currently able to serve traffic. **NOT YET EXECUTED** — to
be configured in Step 8 of `docs/DEPLOYMENT.md` once the ALB exists.

## Operational interpretation

If the health check starts failing, the most likely cause given this
architecture is either the RDS instance being unreachable (security
group misconfiguration, RDS down) or the backend container failing to
start (bad environment variable, image build issue) — both directly
visible in the CloudWatch log stream via the query above, and both
directly testable locally with `docker compose logs backend`.
