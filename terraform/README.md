# terraform/

- `modules/`: `bucket`, `namespace` (namespace + quota + LimitRange + RoleBinding), helm-release wrappers
- `homelab/`: k3s environment, pg backend on Postgres **outside** the cluster (S14, Fri Dec 4)
- `aws/`: EKS environment in us-east-2, **plan only**, S3 backend (S23, Dec 14–15)

Ownership boundary: Terraform owns foundations (namespaces, quotas, RBAC, buckets, the Argo CD install + root app). Argo CD owns every workload. Nothing is owned by both.
