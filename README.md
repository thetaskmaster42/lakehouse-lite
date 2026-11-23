# lakehouse-lite

A small data platform on k3s that turns raw events (NYC taxi trips, Open-Meteo weather, GH Archive) into queryable Iceberg tables. It is shipped entirely through GitOps and watched with Prometheus. This is the capstone for a 4-week Platform Engineer (Data Analytics) interview refresher, **Mon Nov 23 → Fri Dec 18, 2026**.

- **Plan (source of truth for specs, playbooks and failure tests):** https://claude.ai/artifact/5XxsksxCZkAHtyhaMULADk
- **Daily tracker:** [notes/tracker.md](notes/tracker.md). Run `make today` each morning and `make status` for overall progress.

## Daily loop

1. `make today`: see today's spec tasks, acceptance criteria, playbooks, drill, plus anything overdue.
2. Build → tick boxes in `notes/tracker.md` as acceptance criteria pass.
3. Close the day: commit that meets acceptance · one drill aloud in under 3 min · a line in `notes/log.md`.

## Weeks

| Week | Dates | Focus | Specs | Milestone |
|------|-------|-------|-------|-----------|
| 1 | Nov 23–29 | Kubernetes | S0–S9 | Cluster, storage, Postgres, Spark; first curated table |
| 2 | Nov 30–Dec 6 | CI/CD + IaC | S10–S15 | No manual changes; Trino queries the lake |
| 3 | Dec 7–13 | Prometheus, Grafana, OTel | S16–S22 | Dashboards, SLO alerts, game day passed |
| 4 | Dec 14–18 | AWS + mock interviews | S23–S24 | AWS mapping, EKS plan, demo-ready repo |
| Buffer | Dec 19–20 | Rest, weakest drill, optional EKS deploy | — | — |

## Repo layout

```
bootstrap/            # one-time scripts: k3s install, Argo CD bootstrap (S1, S12)
terraform/
  modules/            # bucket, namespace, helm-release wrappers
  homelab/            # k3s environment (S14)
  aws/                # EKS environment, plan only (S23)
gitops/
  apps/               # Argo CD Application manifests (app-of-apps root)
  platform/           # seaweedfs, cnpg, spark-operator, trino, monitoring values
  overlays/{dev,prod}/
charts/spark-job/     # Helm chart for SparkApplications (S13)
jobs/
  ingest/             # Python ingest jobs (S8)
  transform/          # PySpark transform job (S9)
observability/
  rules/              # PrometheusRules + promtool tests (S17, S18, S21)
  dashboards/         # Grafana JSON (S19)
chaos/                # Chaos Mesh experiments, one per FT ID (S22)
playbooks/            # one markdown file per playbook ID (22) + TEMPLATE.md
notes/                # tracker, log, versions, promql, failure-tests, mocks, aws-mapping, sources
scripts/              # progress.py (tracker), backfill.sh (PL-2)
.github/workflows/    # CI (S10, S11)
```

## Conventions

- Namespaces: `platform`, `data`, `monitoring`, `chaos`, `team-a`, `team-b`. Buckets: `raw`, `curated`, `tfstate`, `pg-backups`. Iceberg catalog: `lake`.
- **Ownership boundary:** Terraform owns foundations (namespaces, quotas, RBAC, buckets, the Argo CD install and its root app). Argo CD owns every workload. Nothing is owned by both.
- **Versions:** pin every chart, image and provider to the latest stable release on install day and record it in [notes/versions.md](notes/versions.md). No `latest` tags.
- **Secrets:** never in plaintext in git. Use SealedSecrets only (S5).

## Playbooks

| Infra | Deployment | Pipelines | Monitoring |
|-------|-----------|-----------|------------|
| [IN-1](playbooks/IN-1.md) Rebuild cluster | [DP-1](playbooks/DP-1.md) Ship a change | [PL-1](playbooks/PL-1.md) New source | [MN-1](playbooks/MN-1.md) Scrape target |
| [IN-2](playbooks/IN-2.md) Node drain/replace | [DP-2](playbooks/DP-2.md) Roll back | [PL-2](playbooks/PL-2.md) Backfill | [MN-2](playbooks/MN-2.md) Alert rule |
| [IN-3](playbooks/IN-3.md) Rotate secrets | [DP-3](playbooks/DP-3.md) Promote dev → prod | [PL-3](playbooks/PL-3.md) Failed/late run | [MN-3](playbooks/MN-3.md) Freshness page |
| [IN-4](playbooks/IN-4.md) Object store capacity | [DP-4](playbooks/DP-4.md) Onboard team/job | [PL-4](playbooks/PL-4.md) Schema change | [MN-4](playbooks/MN-4.md) Cardinality |
| [IN-5](playbooks/IN-5.md) Postgres restore | [DP-5](playbooks/DP-5.md) Terraform + drift | [PL-5](playbooks/PL-5.md) DQ triage | [MN-5](playbooks/MN-5.md) Maintenance window |
| [IN-6](playbooks/IN-6.md) Upgrade k3s | | | [MN-6](playbooks/MN-6.md) Dashboard change |
