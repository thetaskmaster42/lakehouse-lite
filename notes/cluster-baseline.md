# Homelab cluster baseline (checked 2026-11-23)

Bootstrap is done outside this repo. The cluster is **pre-existing and shared** with other homelab apps.

## Nodes

| Node | Role | IP | CPU | Memory | Arch |
|------|------|----|-----|--------|------|
| k3s-server | control-plane | 192.168.11.7 | 4 | 16 Gi | arm64 (Raspberry Pi) |
| k3s-worker-1 | worker | 192.168.11.6 | 4 | 16 Gi | arm64 |
| k3s-worker-2 | worker | 192.168.11.5 | 4 | 16 Gi | arm64 |

k3s v1.36.3+k3s1 · Ubuntu 26.04 · containerd 2.3.2-k3s2 · total 12 CPU / 48 Gi · idle usage ~9 Gi.

## Already installed (managed by an existing Argo CD `root` app)

| Component | Namespace | Plan spec it overlaps |
|-----------|-----------|-----------------------|
| Argo CD v3.5.1 (Helm chart argo-cd 10.4.0) + root app-of-apps | argocd | S12 (bootstrap step already done) |
| cert-manager (+ config) | cert-manager | S4 (cert-manager part) |
| CloudNativePG operator + Barman Cloud plugin | cnpg-system | S3 (operator part; `pg-lake` Cluster still needed) |
| kube-prometheus-stack | monitoring | S16 (install part; ServiceMonitors, k3s scrape fixes still needed) |
| Traefik (standalone, not k3s-bundled) | traefik | S4 (ingress part) |
| MetalLB, Tailscale operator | metallb-system, tailscale | not in plan: LoadBalancer IPs + remote access |
| NFS provisioner → TrueNAS (`truenas` StorageClass) | storage | S2 PVC choice |

Other tenants: drawio, excalidraw, headlamp, memos, opengym, rh-dashboard.

## Implications for the plan

1. **Arm64 only.** Every image must have an arm64 build (`apache/spark` and Trino do). S11 already builds amd64 + arm64.
2. **Reuse the existing Argo CD.** Add lakehouse-lite as a child Application (pointing at `gitops/apps/`) under the existing `root`, rather than bootstrapping a second Argo CD. S12's sync waves/AppProjects still apply.
3. **Ownership boundary (S14).** Argo CD was Helm-installed and is managed from another repo. Decide whether Terraform takes it over (`import`) or the boundary note says "Argo CD install is owned by the homelab repo." Don't let two tools own it.
4. **Namespace names.** Plan uses `platform`; operators already live in `cnpg-system`, `cert-manager`, `monitoring`. Keep existing operator namespaces and use `platform` only for new lakehouse components (SeaweedFS, Spark Operator, Trino, Sealed Secrets).
5. **Two default StorageClasses.** Both `local-path` and `truenas` are marked default. PVCs without `storageClassName` become ambiguous, so set `storageClassName` explicitly on every PVC (local-path for SeaweedFS volumes / Prometheus, or truenas for anything that must survive a node loss).
6. **Shared cluster safety.** Chaos Mesh must stay limited to annotated namespaces. Never inject into argocd, kube-system, storage, or other tenants. FT-I1 (power off a worker) affects the other apps too.
7. **PSA.** No namespace has Pod Security labels yet. Apply them only to the plan's namespaces (not to existing tenants) unless you check those first.

## Health notes (not plan work)

- Most pods restarted ~3 h before the check, which looks like a cluster reboot. High lifetime restart counts on argocd-repo-server (2691), cert-manager-cainjector, cloudnative-pg, kube-state-metrics: worth a look in Week 3 as a real MN-4/IN-2 story.
- `memos` is in CrashLoopBackOff and its CNPG cluster `memos-pg` reports "Instance Status Extraction Error".
