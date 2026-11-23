# Homelab → AWS mapping (S23)

| Homelab | AWS managed equivalent | Trade-off | Est. monthly cost |
|---------|------------------------|-----------|-------------------|
| k3s | EKS + Karpenter | Managed control plane and upgrades vs cost and less control | |
| SeaweedFS (S3 API) | S3 | Same API; add lifecycle rules + Intelligent-Tiering | |
| Spark Operator | EMR on EKS / EMR Serverless | Shared cluster and tuning vs zero ops and per-job billing | |
| Trino + Iceberg JDBC catalog | Athena + Glue Data Catalog | Pay per TB scanned; partitioning + compaction cut cost | |
| CloudNativePG | RDS / Aurora PostgreSQL | Backups, failover and patching handled | |
| Prometheus + Grafana | Amazon Managed Prometheus + Managed Grafana | No scaling/retention work; cost scales with series | |
| Loki | CloudWatch Logs, or Loki on S3 | Simplicity vs query cost at volume | |
| Sealed Secrets | Secrets Manager + External Secrets Operator | Rotation and audit built in | |
| GHCR | ECR | IAM-native pulls; built-in scanning | |
| Chaos Mesh | AWS Fault Injection Service | Managed, with CloudWatch-alarm stop conditions | |
