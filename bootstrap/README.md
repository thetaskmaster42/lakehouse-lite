# bootstrap/

**Status: complete (outside this repo).** The homelab k3s cluster (v1.36.3+k3s1, 3 Raspberry Pi nodes, arm64) already exists, kubeconfig is set, and Argo CD is already installed with a root app-of-apps. See [../notes/cluster-baseline.md](../notes/cluster-baseline.md) for what's installed and how it changes the plan.

What's still to put here for S1:

- `cluster-baseline.yaml`: plan namespaces (platform, data, chaos, team-a, team-b) with `team=<name>` and Pod Security labels
- node labels/taint commands (`node-role/data=true`, `workload=batch:NoSchedule`)
- the datastore backup procedure (k3s etcd snapshot or SQLite + token), referenced by IN-1
