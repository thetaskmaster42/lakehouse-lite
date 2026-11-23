# Failure test results

Score each 0–2: detect (alert on time) · diagnose (root cause within 15 min) · recover (within target, via playbook) · learn (follow-up committed). Pass = 6 or more, with no zero.

| FT ID | Scenario | Planned | Run date | Detect time | Diagnose time | Recover time | D/D/R/L | Pass? | Follow-ups |
|-------|----------|---------|----------|-------------|---------------|--------------|---------|-------|------------|
| FT-I1 | Worker node lost | Dec 13 | | | | | | | |
| FT-I2 | Node memory pressure | Dec 13 | | | | | | | |
| FT-I3 | Object store disk filling | Dec 13 | | | | | | | |
| FT-I4 | Postgres primary lost | Dec 13 | | | | | | | |
| FT-I5 | Concurrent Terraform apply + drift | Dec 6 | | | | | | | |
| FT-I6 | Object store gateway down | Dec 13 | | | | | | | |
| FT-I7 | Sealing key lost (k3d only) | Dec 13 | | | | | | | |
| FT-A1 | Crash loop from missing config | Nov 29 | | | | | | | |
| FT-A2 | Bad input data | Nov 29 | | | | | | | |
| FT-A3 | Spark executor out of memory | Nov 29 | | | | | | | |
| FT-A4 | Bad image release | Dec 6 | | | | | | | |
| FT-A5 | Manual drift | Dec 6 | | | | | | | |
| FT-A6 | Broken manifest merged | Dec 6 | | | | | | | |
| FT-A7 | Upstream API outage | Dec 13 | | | | | | | |
| FT-A8 | Runaway query | Dec 13 | | | | | | | |
| FT-N1 | Over-tight NetworkPolicy | Nov 29 | | | | | | | |
| FT-N2 | DNS egress blocked | Nov 29 | | | | | | | |
| FT-N3 | CoreDNS outage | Dec 13 | | | | | | | |
| FT-N4 | Service selector mismatch | Dec 13 | | | | | | | |
| FT-N5 | Latency and packet loss to storage | Dec 13 | | | | | | | |
| FT-N6 | Ingress / TLS failure | Dec 13 | | | | | | | |
| FT-N7 | Egress to the data source blocked | Dec 13 | | | | | | | |
