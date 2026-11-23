# gitops/

- `apps/`: Argo CD Application manifests (app-of-apps root), S12
- `platform/`: values for seaweedfs, cnpg, spark-operator, trino, monitoring
- `overlays/dev`: replay every 15 min, 1 executor, batch-low (S13)
- `overlays/prod`: daily 02:00, 3 executors, batch-high, **manual sync** (S13)

Sync waves: -2 CRDs/operators · -1 SealedSecrets · 0 platform · 1 data jobs · 2 monitoring content.
