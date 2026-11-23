.PHONY: help today status verify lint test plan kubeconfig

help:  ## list targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

today:  ## today's open items + overdue items from notes/tracker.md
	@python3 scripts/progress.py today

status:  ## per-week and overall progress
	@python3 scripts/progress.py status

verify:  ## run automated checks and tick passing items (ARGS=--dry-run|--all|--recheck)
	@python3 scripts/verify.py $(ARGS)

lint:  ## run every pre-commit hook on all files
	pre-commit run --all-files

test:  ## unit tests for jobs (S8) + promtool rule tests (S18)
	@if ls jobs/ingest/*.py >/dev/null 2>&1; then pytest jobs; else echo "no python tests yet (S8)"; fi
	@if ls observability/rules/*test*.y*ml >/dev/null 2>&1; then promtool test rules observability/rules/*test*.y*ml; else echo "no promtool tests yet (S18)"; fi

plan:  ## terraform plan for the homelab env (S14)
	terraform -chdir=terraform/homelab init -input=false
	terraform -chdir=terraform/homelab plan

kubeconfig:  ## fetch k3s kubeconfig: make kubeconfig K3S_SERVER=user@host
	@test -n "$(K3S_SERVER)" || (echo "usage: make kubeconfig K3S_SERVER=user@host" && exit 1)
	ssh $(K3S_SERVER) 'sudo cat /etc/rancher/k3s/k3s.yaml' | sed "s/127.0.0.1/$(lastword $(subst @, ,$(K3S_SERVER)))/" > $(HOME)/.kube/lakehouse-lite.yaml
	@echo "export KUBECONFIG=$(HOME)/.kube/lakehouse-lite.yaml"
