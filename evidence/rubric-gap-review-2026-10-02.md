# Rubric Gap Review - 2026-10-02

## Source reviewed

The six-page `INF2006 Team Project 2026` brief was reviewed against the current
repository. The rubric requires one meaningful analytics or AI capability; it
does not require the four named analytics categories. The project nevertheless
now maps descriptive, diagnostic, predictive, and prescriptive support to real
implemented outputs with explicit limitations.

## Criterion mapping

| Criterion | Current evidence | Remaining submission risk |
|---|---|---|
| Problem framing and architecture | `README.md`, `report.md`, `project_manifest.yaml`, numbered diagrams and trade-off review | Rehearse a concise user-problem-first explanation rather than listing AWS services |
| Cloud implementation and functionality | Source, Terraform, functional evidence, reproducible deployment guide | Stack is intentionally destroyed; retain dated evidence and redeploy only for final demonstration if needed |
| Cloud data and analytics/AI | Provenance, dictionary, Glue/Athena evidence, evaluated model, synthetic offline path, four-category decision flow | Do not present synthetic metrics as model quality or diagnostic associations as causal findings |
| Security and responsible practice | Threat-control map, scoped Lambda roles, JWT routes, user-keyed data access, private origins, encryption, security tests | IAM user access for teammates remains an operator responsibility outside source control |
| Scalability, resilience and operations | Load/resilience records, alarms, dashboard, recovery settings, cost review | Cross-region recovery remains a documented design rather than an exercised deployment |
| Engineering and reproducibility | Manifest, pinned dependencies, local preflight, deterministic sample, CI/security workflows | Build the final ZIP from tracked files and run the preflight against the ZIP contents |
| Team contribution and communication | Required contribution file and AI declaration exist | Blank member roles and contribution rows are the largest remaining marking risk and must be completed truthfully by the team |

## Local verification performed

Command:

```text
python tests/local_preflight.py --include-ml
```

Observed result on 2026-10-02:

- 37 unit tests passed.
- Python source compilation passed.
- 12 manifest paths resolved.
- Five frontend JavaScript files passed `node --check`.
- `terraform fmt -check -recursive` and `terraform validate` passed.
- The deterministic 500-row synthetic sample completed candidate model
  training, evaluation, selection, and artifact export.

The synthetic run selected histogram gradient boosting from 390 scoped training
rows and 98 test rows. Its high synthetic score is not cited as real-world
performance because the sample was generated from a deliberately learnable
formula.

## Priority before submission

1. Complete genuine member roles, artefacts, tests, and reflections in
   `TEAM_CONTRIBUTIONS.md`.
2. Record the final demonstration link or explicitly retain the placeholder if
   no video is submitted.
3. Build the exact submission ZIP from tracked files, scan it for secrets and
   excluded state, then run the local preflight from the extracted ZIP.
4. Recheck `report.pdf` after any later report text change; the 2026-10-02
   version was regenerated and visually reviewed across all ten pages.
