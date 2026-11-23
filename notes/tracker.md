# Daily tracker — Platform Engineer (Data Analytics) Interview Refresher

Plan: https://claude.ai/artifact/5XxsksxCZkAHtyhaMULADk · Mon Nov 23 → Fri Dec 18, 2026 (26 study days) · Buffer Dec 19–20

How to use it:
- Tick `- [x]` as you go. A spec counts as done only when **every** acceptance box under it is ticked and committed.
- Run `make today` each morning for today's open items plus anything overdue. Run `make status` for overall progress.
- Every day ends with the three **Close** boxes: a commit that meets acceptance, one drill answered aloud in under 3 min, and a line in `notes/log.md`.
- Budget: about 2 h on weekdays, 4 h on weekend days, 1 h on Thanksgiving.

---

# Week 1 — Kubernetes (S0–S9)

Milestone: SeaweedFS + Postgres on PVs; Spark writes `lake.taxi.trips`; quotas + default-deny on `data`.

## Day 1 — 2026-11-23 Mon · Architecture

Concepts: API server, etcd (k3s: SQLite or embedded etcd), scheduler, controller manager, kubelet, kube-proxy; reconciliation loops

**S0 Repo and conventions**
- [x] Layout, README.md, notes/log.md, notes/versions.md, playbooks/TEMPLATE.md
- [ ] Pre-commit installed (`pre-commit autoupdate && pre-commit install`): yamllint, terraform fmt, ruff, kubeconform, gitleaks
- [ ] Push to GitHub (`lakehouse-lite`, private) and protect `main` (PRs only)
- [x] Makefile targets: lint, test, plan, kubeconfig
- [ ] ✅ `pre-commit run --all-files` passes on a clean clone
- [ ] ✅ Committing a fake AWS key is blocked by gitleaks

**S1 Cluster baseline**
- [x] k3s installed (pre-existing homelab: v1.36.3+k3s1, 1 server + 2 workers, Raspberry Pi arm64, 4 CPU / 16 Gi each); version in versions.md
- [ ] Agent labels `node-role/data=true`; one agent tainted `workload=batch:NoSchedule`
- [ ] Namespaces platform, data, monitoring, chaos, team-a, team-b with label `team=<name>`
- [ ] PSA baseline on all namespaces, restricted on team-*
- [ ] Datastore backup (etcd snapshot, or SQLite file + server token)
- [ ] ✅ `kubectl get nodes -o wide`: all Ready, with labels and taint
- [ ] ✅ A privileged pod in team-a is rejected by PSA
- [x] ✅ Rebuilding from `bootstrap/` alone gives the same cluster *(bootstrap handled outside this repo; treated as complete)*

**Playbooks**
- [ ] Write IN-1
- [ ] Write IN-2 *(not in the daily grid; written with S1 per Playbooks tab)*
- [ ] Write IN-6 *(not in the daily grid; written with S1 per Playbooks tab)*

**Close**
- [ ] Drill aloud: What happens after `kubectl apply` of a Deployment?
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 2 — 2026-11-24 Tue · Workloads

Concepts: Pods, Deployments, StatefulSets, DaemonSets, Jobs, CronJobs; probes; rolling updates; operators for stateful apps

**S2 Object store (SeaweedFS)**
- [ ] Helm install in platform; volume servers on 50 Gi PVCs on data nodes
- [ ] S3 gateway identities from a Secret: spark-rw, trino-ro, terraform, cnpg
- [ ] Buckets raw, curated, tfstate, pg-backups (by hand; Terraform imports in S14)
- [ ] Path-style, endpoint `http://seaweedfs-s3.platform.svc:8333`
- [ ] ✅ `aws s3 ls --endpoint-url …` works per identity; trino-ro is denied writes
- [ ] ✅ Deleting the S3 gateway pod loses no data

**S3 Metadata database (CloudNativePG)**
- [ ] Operator in platform; Cluster `pg-lake` in data, 2 instances, 10 Gi, PDB
- [ ] DBs iceberg_catalog (owner iceberg) and grafana (owner grafana)
- [ ] WAL archiving + daily base backup to pg-backups
- [ ] Services pg-lake-rw / pg-lake-ro; apps use -rw
- [ ] ✅ Deleting the primary promotes the replica; clients reconnect in under 60 s
- [ ] ✅ Restoring last night's backup into a new Cluster works (IN-5)

**Playbooks**
- [ ] Write IN-4
- [ ] Write IN-5 *(written with S3 per Playbooks tab)*

**Close**
- [ ] Drill aloud: Deployment or StatefulSet for a metadata DB, and why?
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 3 — 2026-11-25 Wed · Networking

Concepts: Service types, CoreDNS, Ingress vs Gateway API, CNI (Flannel), NetworkPolicy enforcement

**S4 Ingress and network policy**
- [ ] Hostnames grafana.lab, argocd.lab, trino.lab, s3.lab; cert-manager self-signed CA
- [ ] Default-deny (ingress + egress) in data, team-a, team-b
- [ ] Allow: DNS 53 UDP/TCP to kube-system; data → SeaweedFS 8333; data → pg-lake 5432; monitoring → metrics ports; ingest egress 443
- [ ] ✅ Test pod in team-a can't reach pg-lake; a pod in data can
- [ ] ✅ Every UI loads over HTTPS by hostname

**Close**
- [ ] Drill aloud: A pod can't reach a Service. Debug it step by step
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 4 — 2026-11-26 Thu · Storage and config (Thanksgiving, 1 h)

Concepts: PV, PVC, StorageClass (local-path), CSI, access modes; ConfigMaps, Secrets, sealed vs external secrets

**S5 Secrets management**
- [ ] Sealed Secrets controller in platform; seal SeaweedFS identities, Postgres creds, Grafana admin
- [ ] Sealing key backed up offline
- [ ] ✅ `git grep -i password` finds no plaintext values
- [ ] ✅ Restoring the sealing key on a fresh cluster decrypts existing SealedSecrets

**Playbooks**
- [ ] Write IN-3

**Close**
- [ ] Drill aloud: How do you keep secrets out of git and still do GitOps?
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 5 — 2026-11-27 Fri · Scheduling and tenancy

Concepts: requests/limits, QoS, HPA/VPA, Cluster Autoscaler vs Karpenter, taints, affinity, PDBs, PriorityClass

**S6 Tenancy and capacity controls**
- [ ] Quotas team-a/team-b: 4 CPU, 8 Gi, 10 pods, 2 PVCs; larger quota for data
- [ ] LimitRange defaults: 250m/256Mi requests, 1 CPU/1Gi limits
- [ ] PriorityClasses platform-critical, batch-high, batch-low (preemptible)
- [ ] RBAC: team-a-dev gets edit in team-a + read-only nodes ClusterRole
- [ ] ✅ A 5-CPU job in team-a is rejected by quota
- [ ] ✅ A batch-low pod is preempted by batch-high
- [ ] ✅ `kubectl auth can-i` as team-a-dev shows no access to team-b

**Close**
- [ ] Drill aloud: Spark executors keep getting OOMKilled. What do you check?
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 6 — 2026-11-28 Sat · Extending Kubernetes (4 h)

Concepts: CRDs, operators, admission webhooks, Helm vs Kustomize; Spark driver and executor pods

**S7 Spark platform**
- [ ] Spark Operator in platform watching data, team-a, team-b; SA `spark` + Role in each
- [ ] Image `lakehouse-spark`: apache/spark Python + iceberg-spark-runtime + iceberg-aws-bundle + PG JDBC (versions per Iceberg matrix)
- [ ] Drivers on untainted nodes; executors tolerate workload=batch + prefer batch node
- [ ] PrometheusServlet on driver
- [ ] ✅ SparkPi SparkApplication shows COMPLETED
- [ ] ✅ Executors land on the batch node; driver doesn't
- [ ] ✅ Deleting an executor mid-job: job still succeeds

**S8 Ingest jobs**
- [ ] ingest-tlc (monthly + replay every 15 min in dev)
- [ ] ingest-weather (Open-Meteo /v1/archive, NYC)
- [ ] ingest-zones (weekly) and ingest-gharchive (on demand)
- [ ] `_manifest.json` per run; skip if same sha256
- [ ] HTTP: 30 s timeout, 3 retries with backoff + jitter on 5xx/timeouts; fail fast on 4xx
- [ ] CronJob: concurrencyPolicy Forbid, backoffLimit 2, activeDeadlineSeconds 1800, startingDeadlineSeconds 300; JSON logs
- [ ] ✅ Same month twice: no new objects; logs `skipped: unchanged`
- [ ] ✅ 2099-01 exits non-zero with `source_not_found`
- [ ] ✅ `pytest jobs/ingest` passes, incl. mocked-503 retry test

**Close**
- [ ] Drill aloud: When would you write an operator rather than a Helm chart?
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 7 — 2026-11-29 Sun · Security + break-fix (4 h)

Concepts: RBAC, ServiceAccounts, Pod Security Admission; CrashLoopBackOff, Pending, ImagePullBackOff, DNS failures

**S9 Transform job (raw → Iceberg)**
- [ ] Catalog `lake` (JDBC on pg-lake-rw, warehouse s3://curated/warehouse, S3FileIO, path-style)
- [ ] Date-arg job: cast to contract schema, add ingest_run_id
- [ ] DQ rules → lake.quarantine.trips_rejected with reject_reason
- [ ] Fail if more than 2% rejected (threshold in config)
- [ ] Dynamic partition overwrite per day; rebuild marts.daily_zone_stats joined to weather
- [ ] Weekly maintenance: expire_snapshots (7 d) + rewrite_data_files
- [ ] ✅ Same date twice: identical row counts in every table
- [ ] ✅ 5% bad rows fails the run; rows land in quarantine
- [ ] ✅ `lake.taxi.trips.snapshots` shows one snapshot per run

**Failure tests (break-fix lab)** → record in notes/failure-tests.md
- [ ] FT-A1 Crash loop from missing config
- [ ] FT-A2 Bad input data
- [ ] FT-A3 Spark executor OOM
- [ ] FT-N1 Over-tight NetworkPolicy
- [ ] FT-N2 DNS egress blocked

**Close**
- [ ] Drill aloud: Design a cluster shared by 5 analytics teams
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md
- [ ] 🏁 Week 1 milestone met

---

# Week 2 — CI/CD and IaC (S10–S15)

Milestone: Terraform owns buckets, namespaces, Helm releases; CI tests/scans/signs/pushes; Argo CD syncs all apps; Trino queries the lake.

## Day 8 — 2026-11-30 Mon · GitHub Actions

Concepts: workflows, matrix, caching, reusable workflows, environments + approvals, OIDC, ARC runners

**S10 CI pipelines**
- [ ] ci.yml with path filters: pre-commit; pytest; helm lint + template | kubeconform; terraform fmt/validate/tflint
- [ ] Reusable workflows `_python.yml`, `_k8s-validate.yml`; concurrency cancel-in-progress; pip + provider cache
- [ ] One ARC runner scale set in namespace `ci` (repo private or trusted branches only)
- [ ] Required status checks on main
- [ ] ✅ PR with a failing unit test can't merge
- [ ] ✅ PR touching only observability/ skips Python + Terraform jobs
- [ ] ✅ Median CI time under 5 min (recorded in log.md)

**Close**
- [ ] Drill aloud: Why OIDC instead of access keys in CI secrets?
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 9 — 2026-12-01 Tue · Supply chain

Concepts: multi-stage Dockerfiles, buildx, Trivy, SBOMs, cosign, tag vs digest pinning

**S11 Image supply chain**
- [ ] build.yml: lakehouse-spark + lakehouse-ingest for amd64 + arm64 with cache
- [ ] Trivy: fail on fixable CRITICAL; SARIF upload; SBOM attached
- [ ] cosign keyless sign; tag sha-<short>; deploy by digest
- [ ] Bot PR bumps digest in gitops/overlays/dev
- [ ] ✅ `cosign verify` with workflow identity succeeds on a deployed digest
- [ ] ✅ Old base image with a known critical CVE fails the build

**Close**
- [ ] Drill aloud: How do you trust what's running in production?
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 10 — 2026-12-02 Wed · GitOps

Concepts: Argo CD vs Flux, app-of-apps, sync waves, self-heal + prune, drift; rolling/blue-green/canary

**S12 GitOps with Argo CD**
- [ ] Bootstrap Argo CD with Helm; root Application → gitops/apps/
- [ ] Sync waves -2 / -1 / 0 / 1 / 2
- [ ] Platform apps auto-sync + prune + selfHeal; prod manual sync
- [ ] AppProjects platform, team-a, team-b
- [ ] ignoreDifferences documented per field
- [ ] ✅ Manual `kubectl scale` reverted by self-heal within 3 min
- [ ] ✅ Removing a manifest from git prunes its resources
- [ ] ✅ team-a Application targeting team-b is refused

**Playbooks**
- [ ] Write DP-1
- [ ] Write DP-2

**Close**
- [ ] Drill aloud: Push-based deploys vs GitOps: trade-offs?
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 11 — 2026-12-03 Thu · Helm and Kustomize

Concepts: chart structure, values schema, templating pitfalls, library charts; overlays and patches

**S13 Packaging: Helm chart + Kustomize overlays**
- [ ] charts/spark-job renders ScheduledSparkApplication from values
- [ ] values.schema.json (schedule, image.digest, resources required); helm-unittest tests
- [ ] Overlays dev (15 min, 1 exec, batch-low) and prod (02:00, 3 exec, batch-high)
- [ ] Golden-path README: zero → running in 5 steps
- [ ] ✅ `helm template` fails without image.digest
- [ ] ✅ `kustomize build` dev vs prod render different schedules + resources

**Playbooks**
- [ ] Write DP-3
- [ ] Write DP-4 *(written with S6/S13 per Playbooks tab)*

**Close**
- [ ] Drill aloud: When do you pick Helm, Kustomize, or both?
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 12 — 2026-12-04 Fri · Terraform

Concepts: state, backends + locking, modules, env layout, plan in PR, drift, import + moved blocks; CFN/CDK/Pulumi

**S14 Terraform foundations**
- [ ] pg backend on an off-cluster Postgres (DGX Spark container or NAS)
- [ ] Modules namespace + bucket; env terraform/homelab with Argo CD release + root app
- [ ] import blocks for existing resources; moved blocks for renames
- [ ] CI: plan on ARC runner posted to PR; apply behind Environment approval; nightly drift plan
- [ ] Note any SeaweedFS/AWS-provider gaps in notes/
- [ ] ✅ After imports, `terraform plan` shows no changes
- [ ] ✅ A second concurrent apply waits on the lock
- [ ] ✅ Hand-added label on team-a flagged by nightly drift

**Playbooks**
- [ ] Write DP-5

**Close**
- [ ] Drill aloud: Two engineers applied at once and state is corrupt. Now what?
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 13 — 2026-12-05 Sat · CI/CD for data teams (4 h)

Concepts: testing data code, DQ gates, schema evolution, deploying DAGs, preview envs

**S15 Query layer (Trino)**
- [ ] Trino Helm (coordinator + 2 workers); lake.properties Iceberg JDBC + native S3 + trino-ro SealedSecret
- [ ] Resource groups: team-a/team-b 2 concurrent + 40% memory; adhoc 1
- [ ] Ingress trino.lab with password auth
- [ ] ✅ `SELECT borough, sum(trips) FROM lake.marts.daily_zone_stats GROUP BY 1` returns rows
- [ ] ✅ EXPLAIN on a date filter shows partition pruning
- [ ] ✅ Third concurrent team-a query queues

**Playbooks**
- [ ] Write PL-1
- [ ] Write PL-2
- [ ] Write PL-4

**Close**
- [ ] Drill aloud: Design CI/CD for 30 data engineers shipping DAGs and Spark jobs
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 14 — 2026-12-06 Sun · End-to-end + failure drills (4 h)

Concepts: rollback paths, least-privilege tokens, protected branches, DORA metrics

**End to end**
- [ ] A one-line change reaches the cluster with no manual step

**Failure tests (delivery drills)** → record in notes/failure-tests.md
- [ ] FT-A4 Bad image release
- [ ] FT-A5 Manual drift
- [ ] FT-A6 Broken manifest merged
- [ ] FT-I5 Concurrent Terraform apply + drift

**Close**
- [ ] Drill aloud: Walk me through your deploy pipeline and where it can fail
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md
- [ ] 🏁 Week 2 milestone met

---

# Week 3 — Prometheus, Grafana, OpenTelemetry (S16–S22)

Milestone: pipeline metrics, dashboards, freshness burn-rate alert in git; every failure test passes.

## Day 15 — 2026-12-07 Mon · Prometheus architecture

Concepts: pull model, ServiceMonitor/PodMonitor, exporters, TSDB, metric types, cardinality

**S16 Metrics stack**
- [ ] kube-prometheus-stack via Argo CD; 15 d retention on 20 Gi; Grafana on pg-lake
- [ ] Disable or re-point embedded k3s scrape jobs
- [ ] Monitors: SeaweedFS, CNPG, Trino, Spark driver, Argo CD, Traefik (label monitoring=enabled)
- [ ] ✅ Every target UP
- [ ] ✅ Only Watchdog firing on a healthy cluster

**Playbooks**
- [ ] Write MN-1

**Close**
- [ ] Drill aloud: Why pull instead of push? When is Pushgateway right?
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 16 — 2026-12-08 Tue · PromQL

Concepts: rate/irate/increase, by/without, histogram_quantile, absent, offset, subqueries, recording rules

**S17 Pipeline metrics and recording rules**
- [ ] Jobs push to Pushgateway (grouping key job + pipeline; no run_id label)
- [ ] Metrics: rows_processed_total, rows_rejected_total, last_success_timestamp_seconds, last_run_status, duration_seconds histogram
- [ ] Recording rules: freshness_seconds, reject_ratio:1h, duration p95_1d, cronjob last_success_age
- [ ] 10 queries with explanations in notes/promql.md
- [ ] ✅ Each recording rule returns a series per pipeline
- [ ] ✅ pipeline_* series count flat across 20 runs

**Close**
- [ ] Drill aloud: Write p95 job duration per pipeline
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 17 — 2026-12-09 Wed · Alerting

Concepts: Alertmanager routing/grouping/inhibition/silences; symptom vs cause; RED/USE; promtool tests

**S18 Alerting rules and routing**
- [ ] Platform rules: PVCFillingUp, NodeDiskPressure, CNPGReplicationLagHigh, SeaweedFSVolumeAlmostFull, ArgoAppDegraded
- [ ] Pipeline rules: PipelineRunFailed, PipelineRejectRatioHigh
- [ ] severity + summary + runbook_url on every rule
- [ ] Alertmanager routing (page → push, ticket → email, inhibition); Watchdog → dead-man's switch
- [ ] promtool tests in CI
- [ ] ✅ CI fails on a failed rule test or missing runbook_url
- [ ] ✅ A failed job reaches your phone within 5 min
- [ ] ✅ Stopping Prometheus triggers the dead-man's switch

**Playbooks**
- [ ] Write MN-2
- [ ] Write MN-5

**Close**
- [ ] Drill aloud: What makes an alert worth waking someone up for?
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 18 — 2026-12-10 Thu · Grafana

Concepts: dashboards as code, provisioning, variables, Grafana alerting vs Alertmanager

**S19 Dashboards as code**
- [ ] Pipeline health dashboard (vars pipeline, namespace)
- [ ] Platform overview dashboard
- [ ] Trino dashboard
- [ ] SLO dashboard (budget + burn rate)
- [ ] ConfigMaps labelled grafana_dashboard=1; UI edits disabled
- [ ] ✅ Deleting Grafana pod + data restores every dashboard from git
- [ ] ✅ Failing pipeline spotted in under 30 s

**Playbooks**
- [ ] Write MN-6

**Close**
- [ ] Drill aloud: Design the first dashboard on-call opens
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 19 — 2026-12-11 Fri · Logs, traces, OpenTelemetry

Concepts: OTel SDK + Collector, context propagation, three signals; Loki vs ELK; Tempo

**S20 Logs and traces**
- [ ] Loki (monolithic) with chunks in SeaweedFS `loki` bucket; 7 d retention
- [ ] Collector DaemonSet: filelog + k8sattributes → Loki OTLP
- [ ] Collector gateway: OTLP traces → Tempo (or debug exporter)
- [ ] Ingest jobs instrumented with OTel Python; trace_id in JSON logs
- [ ] ✅ LogQL returns ingest errors
- [ ] ✅ From an error log line you can open its trace (if Tempo)

**Close**
- [ ] Drill aloud: ELK or Loki for 2 TB/day of logs? Defend it
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 20 — 2026-12-12 Sat · Scaling and SLOs (4 h)

Concepts: HA Prometheus, remote_write, Thanos/Mimir; SLI/SLO, error budgets, multi-window burn rates

**S21 SLOs and burn-rate alerts**
- [ ] Freshness SLI (minutes with freshness < 1800 s), SLO 99% / 7 d
- [ ] Run-success SLI, SLO 99% / 7 d
- [ ] Burn-rate alerts: page 1h & 5m > 14.4; ticket 6h & 30m > 6
- [ ] Error-budget panel on SLO dashboard
- [ ] ✅ Pausing replay 45 min fires the freshness page; resuming resolves it
- [ ] ✅ One failed run doesn't page; repeated failures do

**Playbooks**
- [ ] Write MN-3
- [ ] Write MN-4
- [ ] Write PL-3
- [ ] Write PL-5

**Close**
- [ ] Drill aloud: Prometheus is running out of memory. Diagnose and fix it
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 21 — 2026-12-13 Sun · Game day (4 h)

Concepts: inject failures with Chaos Mesh; find causes from dashboards and alerts only

**S22 Chaos tooling and game day**
- [ ] Chaos Mesh in `chaos` with k3s containerd socket; annotated namespaces only
- [ ] One YAML per FT ID in chaos/
- [ ] Pre-game backups: CNPG backup + etcd/SQLite snapshot
- [ ] ✅ Every FT scenario's "pass when" is met
- [ ] ✅ At least one playbook or alert improved from findings (commit linked in log)

**Failure tests (game day)** → record in notes/failure-tests.md
- [ ] FT-I1 Worker node lost
- [ ] FT-I2 Node memory pressure
- [ ] FT-I3 Object store disk filling
- [ ] FT-I4 Postgres primary lost
- [ ] FT-I6 Object store gateway down
- [ ] FT-I7 Sealing key lost (k3d only)
- [ ] FT-A7 Upstream API outage
- [ ] FT-A8 Runaway query
- [ ] FT-N3 CoreDNS outage
- [ ] FT-N4 Service selector mismatch
- [ ] FT-N5 Latency and packet loss to storage
- [ ] FT-N6 Ingress / TLS failure
- [ ] FT-N7 Egress to data source blocked

**Close**
- [ ] Drill aloud: Tell me about an incident you led, start to finish
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md
- [ ] 🏁 Week 3 milestone met

---

# Week 4 — AWS platform stack + mock interviews (S23–S24)

Milestone: AWS mapping written; EKS Terraform passes plan; README, playbook index, demo script done.

## Day 22 — 2026-12-14 Mon · Foundations + EKS

Concepts: Organizations/SCPs; VPC (private subnets, NAT, S3 gateway endpoint); IAM, permission boundaries; EKS nodes, VPC CNI IP exhaustion, IRSA vs Pod Identity, upgrades

**S23 part 1 — EKS Terraform (us-east-2, plan only)**
- [ ] VPC: 2 AZs, private node subnets, 1 NAT, S3 gateway endpoint
- [ ] EKS: Graviton managed node group; add-ons VPC CNI, CoreDNS, kube-proxy, EBS CSI, Pod Identity agent
- [ ] S3 backend with locking; tags project/env; $10 Budget alert

**Close**
- [ ] Drill aloud: How do you upgrade EKS with zero downtime?
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 23 — 2026-12-15 Tue · Analytics services + cost

Concepts: S3 + Glue + Athena, EMR on EKS vs Serverless, MSK/Kinesis, Redshift, Lake Formation, MWAA, AMP/AMG; Spot, Savings Plans, lifecycle, Graviton

**S23 part 2 — AWS mapping and cost notes**
- [ ] S3 raw/curated: SSE-KMS, public access blocked, raw → IA after 30 d
- [ ] Glue database `lake` + Athena workgroup with scan limit; Spark via Pod Identity
- [ ] notes/aws-mapping.md: homelab → AWS mapping + per-service cost notes
- [ ] ✅ `terraform plan` succeeds and is reviewed in a PR

**Close**
- [ ] Drill aloud: Analytics spend doubled this month. Find out why
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md

## Day 24 — 2026-12-16 Wed · Mock 1: system design

- [ ] 45 min timed mock (question bank) + 45 min review
- [ ] Self-score with rubric → notes/mocks.md

**Close**
- [ ] Log line in notes/log.md

## Day 25 — 2026-12-17 Thu · Mock 2 + Mock 3

- [ ] Mock 2: K8s deep dive + troubleshooting (45 min)
- [ ] Mock 3: behavioral (45 min)
- [ ] Self-score both with rubric → notes/mocks.md

**Close**
- [ ] Log line in notes/log.md

## Day 26 — 2026-12-18 Fri · Polish

**S24 Handoff and demo**
- [ ] README: diagram, ownership boundary, quickstart (IN-1), links to every playbook
- [ ] notes/failure-tests.md results table complete
- [ ] Demo script (commit → CI → Argo → Spark → Trino → Grafana → kill CNPG primary → alert → recovery)
- [ ] Story bank: 6 behavioral prompts mapped
- [ ] Tag v1.0
- [ ] ✅ Demo rehearsed twice, each under 5 min
- [ ] ✅ Cold rebuild from README alone succeeds

**Close**
- [ ] Drill aloud: Present the capstone in 5 minutes
- [ ] Commit meets acceptance
- [ ] Log line in notes/log.md
- [ ] 🏁 Week 4 milestone met

---

# Buffer — Sat–Sun 2026-12-19 → 2026-12-20

- Rest; redo the weakest drill; optional one-day EKS apply + `terraform destroy` (check no NAT/EIP/ENI/LB left)
- Everything unticked below goes here.

# Playbooks run at least once (by Dec 18)

- [ ] IN-1 run
- [ ] IN-2 run
- [ ] IN-3 run
- [ ] IN-4 run
- [ ] IN-5 run
- [ ] IN-6 run
- [ ] DP-1 run
- [ ] DP-2 run
- [ ] DP-3 run
- [ ] DP-4 run
- [ ] DP-5 run
- [ ] PL-1 run
- [ ] PL-2 run
- [ ] PL-3 run
- [ ] PL-4 run
- [ ] PL-5 run
- [ ] MN-1 run
- [ ] MN-2 run
- [ ] MN-3 run
- [ ] MN-4 run
- [ ] MN-5 run
- [ ] MN-6 run

# Readiness checklist (by Fri Dec 18)

- [ ] Explain the path of a `kubectl apply` through the control plane without notes
- [ ] All 24 capstone specs meet their acceptance criteria
- [ ] All 22 playbooks written and each run at least once
- [ ] Every failure test passed, with detection and recovery times logged
- [ ] Write rate, histogram_quantile and burn-rate PromQL from memory
- [ ] Explain why Terraform state needs locking, and recover from a bad apply
- [ ] Draw the capstone and its AWS equivalent on a whiteboard in 5 min
- [ ] Give a cost-reduction story with real numbers
- [ ] Score 3+ on every rubric row across all three mocks
