# Adheesh branch integration review

## Scope

The `origin/adheesh` branch was compared with `nixon` before CI and deployment
work. The review focused on reusable features, architecture compatibility, data
provenance, and alignment with the agreed INF2006 serverless scope.

## Findings

The branch contains a separate StaySphere booking application built around a
FastAPI container, PostgreSQL-style relational models, locally generated dummy
listings and reviews, and booking and administration workflows. Those files do
not extend the current Airbnb Pricing and Market Intelligence Platform. Merging
them into the active runtime would introduce a second API, duplicate model,
conflicting frontend, and unsupported synthetic evidence.

The following ideas are useful but are already represented by current project
artefacts:

- Requirements traceability through `project_manifest.yaml` and the evidence index.
- Explicit cloud trade-off analysis in `evidence/serverless-zero-trust-review.md`.
- Responsible AI limitations in `evidence/test-data-ai.md` and `report.md`.
- Threat-to-control mapping in `evidence/threat-control-map.md`.
- Functional, security, data/AI, and resilience testing under `tests/` and `evidence/`.

## Decision

No StaySphere runtime code or synthetic dataset is included in the `nixon`
application. Adheesh's source remains available on `origin/adheesh` for team
reference. This preserves authorship while keeping the submitted architecture,
dataset claims, tests, and deployment path internally consistent.
