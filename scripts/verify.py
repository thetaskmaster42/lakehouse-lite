#!/usr/bin/env python3
"""Run automated checks for tracker items and tick the ones that pass.

  make verify                 # check open items for days up to today; tick passes
  make verify ARGS=--dry-run  # report only, don't edit tracker.md
  make verify ARGS=--all      # include future days too
  make verify ARGS=--recheck  # also re-run ticked items and report regressions

Safety on the shared cluster: every cluster check is read-only. Admission tests
use `--dry-run=server`, so PSA and ResourceQuota run but nothing is persisted.
The gitleaks test runs in a throwaway temp repo.

Adding a check: write a function returning (ok, detail) and register it in
CHECKS with a substring that matches exactly one tracker line.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import re
import shutil
import string
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACKER = ROOT / "notes" / "tracker.md"
DAY_RE = re.compile(r"^## Day \d+ — (\d{4}-\d{2}-\d{2})")
BOX_RE = re.compile(r"^- \[( |x|X)\] (.*)$")

PLAN_NS = ["platform", "data", "monitoring", "chaos", "team-a", "team-b"]


# ---------------------------------------------------------------- helpers
def run(cmd, cwd=ROOT, timeout=120, input=None):
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            input=input,
            check=False,  # callers inspect the return code themselves
        )
        return p.returncode, (p.stdout + p.stderr).strip()
    except FileNotFoundError:
        return 127, f"{cmd[0]} not installed"
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout}s"


def kjson(*args):
    rc, out = run(["kubectl", *args, "-o", "json"])
    if rc != 0:
        raise RuntimeError(out.splitlines()[-1] if out else "kubectl failed")
    return json.loads(out)


def short(text, n=160):
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1] + "…"


# ---------------------------------------------------------------- Day 1: S0
def c_layout():
    need = [
        "README.md",
        "notes/log.md",
        "notes/versions.md",
        "playbooks/TEMPLATE.md",
        "bootstrap",
        "terraform/modules",
        "gitops/apps",
        "charts/spark-job",
        "jobs/ingest",
        "observability/rules",
        "chaos",
        ".github/workflows",
    ]
    missing = [p for p in need if not (ROOT / p).exists()]
    return (not missing, "all present" if not missing else f"missing: {missing}")


def c_precommit_installed():
    hook = ROOT / ".git" / "hooks" / "pre-commit"
    ok = hook.exists() and "pre-commit" in hook.read_text(errors="ignore")
    return ok, "hook installed" if ok else "run: pre-commit install"


def c_makefile():
    text = (ROOT / "Makefile").read_text()
    missing = [
        t
        for t in ["lint", "test", "plan", "kubeconfig"]
        if not re.search(rf"^{t}:", text, re.MULTILINE)
    ]
    return (
        not missing,
        "targets present" if not missing else f"missing targets: {missing}",
    )


def c_github_protected():
    rc, url = run(["git", "remote", "get-url", "origin"])
    if rc != 0:
        return False, "no git remote 'origin' yet"
    m = re.search(r"github\.com[:/]([^/]+/[^/.]+)", url)
    if not m:
        return False, f"origin is not GitHub: {url}"
    rc, out = run(["gh", "api", f"repos/{m.group(1)}/branches/main/protection"])
    return (
        rc == 0,
        "main is protected" if rc == 0 else f"no protection on main ({short(out, 80)})",
    )


def c_precommit_clean_clone():
    rc, _ = run(["git", "rev-parse", "--verify", "HEAD"])
    if rc != 0:
        return (
            False,
            "no commits yet: commit first, the check runs on a clean clone of HEAD",
        )
    with tempfile.TemporaryDirectory() as tmp:
        rc, out = run(["git", "clone", "-q", str(ROOT), tmp])
        if rc != 0:
            return False, short(out)
        rc, out = run(["pre-commit", "run", "--all-files"], cwd=tmp, timeout=600)
        if rc == 0:
            return True, "all hooks pass on a clean clone"
        failed = [l for l in out.splitlines() if l.rstrip().endswith("Failed")]
        return False, "failing hooks: " + "; ".join(short(l, 60) for l in failed[:5])


def c_gitleaks_blocks():
    # Random but realistic key: gitleaks allowlists AWS's documented example key.
    key = "AKIA" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567", k=16))
    secret = "".join(random.choices(string.ascii_letters + string.digits + "/+", k=40))
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(ROOT / ".pre-commit-config.yaml", tmp)
        run(["git", "init", "-q"], cwd=tmp)
        Path(tmp, "creds.py").write_text(
            f'aws_access_key_id = "{key}"\naws_secret_access_key = "{secret}"\n'
        )
        run(["git", "add", "-A"], cwd=tmp)
        rc, out = run(["pre-commit", "run", "gitleaks"], cwd=tmp, timeout=300)
    if rc == 0:
        return False, "gitleaks did NOT block a fake AWS key"
    if "leaks found" in out.lower() or "Failed" in out:
        return True, "commit with fake AWS key was blocked"
    return False, f"hook errored rather than detecting: {short(out)}"


# ---------------------------------------------------------------- Day 1: S1
def _workers():
    nodes = kjson("get", "nodes")["items"]
    return nodes, [
        n
        for n in nodes
        if "node-role.kubernetes.io/control-plane" not in n["metadata"]["labels"]
    ]


def _has_batch_taint(n):
    return any(
        t.get("key") == "workload"
        and t.get("value") == "batch"
        and t.get("effect") == "NoSchedule"
        for t in n["spec"].get("taints", [])
    )


def c_node_labels_taint():
    _, workers = _workers()
    unlabeled = [
        n["metadata"]["name"]
        for n in workers
        if n["metadata"]["labels"].get("node-role/data") != "true"
    ]
    tainted = [n["metadata"]["name"] for n in workers if _has_batch_taint(n)]
    problems = []
    if unlabeled:
        problems.append(f"missing node-role/data=true on {unlabeled}")
    if not tainted:
        problems.append("no worker tainted workload=batch:NoSchedule")
    return not problems, "; ".join(problems) or f"labels ok; tainted: {tainted}"


def c_nodes_ready_labeled():
    nodes, _ = _workers()
    notready = [
        n["metadata"]["name"]
        for n in nodes
        if not any(
            c["type"] == "Ready" and c["status"] == "True"
            for c in n["status"]["conditions"]
        )
    ]
    ok, detail = c_node_labels_taint()
    if notready:
        return False, f"NotReady: {notready}"
    return ok, ("all Ready; " + detail)


def c_namespaces():
    items = {
        n["metadata"]["name"]: n["metadata"].get("labels", {})
        for n in kjson("get", "ns")["items"]
    }
    missing = [ns for ns in PLAN_NS if ns not in items]
    unlabeled = [ns for ns in PLAN_NS if ns in items and items[ns].get("team") != ns]
    problems = ([f"missing: {missing}"] if missing else []) + (
        [f"no team=<name> label: {unlabeled}"] if unlabeled else []
    )
    return not problems, "; ".join(
        problems
    ) or "all 6 namespaces exist and are labelled"


def c_psa_labels():
    items = {
        n["metadata"]["name"]: n["metadata"].get("labels", {})
        for n in kjson("get", "ns")["items"]
    }
    want = {
        ns: ("restricted" if ns.startswith("team-") else "baseline") for ns in PLAN_NS
    }
    wrong = {
        ns: items.get(ns, {}).get("pod-security.kubernetes.io/enforce", "<none>")
        for ns, level in want.items()
        if items.get(ns, {}).get("pod-security.kubernetes.io/enforce") != level
    }
    return (
        not wrong,
        "PSA enforce labels correct"
        if not wrong
        else f"wrong/missing enforce level: {wrong}",
    )


def c_psa_rejects_privileged():
    rc, out = run(
        [
            "kubectl",
            "run",
            "verify-psa",
            "-n",
            "team-a",
            "--image=busybox",
            "--privileged",
            "--restart=Never",
            "--dry-run=server",
            "--",
            "true",
        ]
    )
    if rc != 0 and "PodSecurity" in out:
        return True, "privileged pod rejected by PSA (server dry-run)"
    if rc == 0:
        return False, "privileged pod was ADMITTED in team-a"
    return False, short(out)


# ---------------------------------------------------------------- Day 2: S3
def c_pg_lake_cluster():
    try:
        c = kjson("get", "clusters.postgresql.cnpg.io", "pg-lake", "-n", "data")
    except RuntimeError as e:
        return False, str(e)
    inst, ready = (
        c["spec"].get("instances"),
        c.get("status", {}).get("readyInstances", 0),
    )
    phase = c.get("status", {}).get("phase", "?")
    ok = inst == 2 and ready == 2
    return ok, f"instances={inst} ready={ready} phase={phase!r}"


def c_pg_lake_services():
    missing = [
        s
        for s in ("pg-lake-rw", "pg-lake-ro")
        if run(["kubectl", "get", "svc", s, "-n", "data"])[0] != 0
    ]
    return not missing, "services present" if not missing else f"missing: {missing}"


# ---------------------------------------------------------------- Day 3: S4
def c_default_deny():
    bad = []
    for ns in ("data", "team-a", "team-b"):
        try:
            pols = kjson("get", "networkpolicy", "-n", ns)["items"]
        except RuntimeError as e:
            return False, str(e)
        if not any(
            p["spec"].get("podSelector", {}) == {}
            and set(p["spec"].get("policyTypes", [])) >= {"Ingress", "Egress"}
            and not p["spec"].get("ingress")
            and not p["spec"].get("egress")
            for p in pols
        ):
            bad.append(ns)
    return (
        not bad,
        "default-deny in all three"
        if not bad
        else f"no default-deny (ingress+egress) in {bad}",
    )


def c_uis_https():
    bad = []
    for host in ("grafana.lab", "argocd.lab", "trino.lab", "s3.lab"):
        rc, code = run(
            [
                "curl",
                "-sk",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                "--max-time",
                "8",
                f"https://{host}/",
            ]
        )
        if rc != 0 or not code.isdigit() or int(code) >= 500 or code == "000":
            bad.append(f"{host}({code or rc})")
    return not bad, "all UIs answer over HTTPS" if not bad else f"not reachable: {bad}"


# ---------------------------------------------------------------- Day 4: S5
def c_no_plaintext_passwords():
    rc, out = run(
        [
            "git",
            "grep",
            "-inE",
            r"(password|passwd|secret_key)\s*[:=]\s*['\"]?[A-Za-z0-9]",
            "--",
            ".",
            ":!*.md",
            ":!scripts/verify.py",
        ]
    )
    hits = [l for l in out.splitlines() if "encryptedData" not in l] if rc == 0 else []
    return (
        not hits,
        "no plaintext password values tracked by git"
        if not hits
        else f"{len(hits)} hit(s): {short(hits[0], 100)}",
    )


# ---------------------------------------------------------------- Day 5: S6
def _quota_pod(cpu):
    return json.dumps(
        {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": "verify-quota", "namespace": "team-a"},
            "spec": {
                "restartPolicy": "Never",
                "securityContext": {
                    "runAsNonRoot": True,
                    "runAsUser": 1000,
                    "seccompProfile": {"type": "RuntimeDefault"},
                },
                "containers": [
                    {
                        "name": "c",
                        "image": "busybox",
                        "command": ["true"],
                        "securityContext": {
                            "allowPrivilegeEscalation": False,
                            "capabilities": {"drop": ["ALL"]},
                        },
                        "resources": {
                            "requests": {"cpu": cpu, "memory": "64Mi"},
                            "limits": {"cpu": cpu, "memory": "64Mi"},
                        },
                    }
                ],
            },
        }
    )


def c_quota_rejects():
    rc, out = run(
        ["kubectl", "apply", "--dry-run=server", "-f", "-"], input=_quota_pod("5")
    )
    if rc != 0 and ("exceeded quota" in out or "forbidden: exceeded" in out):
        return True, "5-CPU pod rejected by ResourceQuota (server dry-run)"
    if rc == 0:
        return False, "5-CPU pod was ADMITTED in team-a"
    if "maximum cpu usage" in out:
        return False, "rejected by LimitRange max, not by quota: check quota exists"
    return False, short(out)


def c_quotas_limitranges_pcs():
    problems = []
    for ns in ("team-a", "team-b"):
        q = kjson("get", "resourcequota", "-n", ns)["items"]
        if not q:
            problems.append(f"no ResourceQuota in {ns}")
        if not kjson("get", "limitrange", "-n", ns)["items"]:
            problems.append(f"no LimitRange in {ns}")
    pcs = {p["metadata"]["name"] for p in kjson("get", "priorityclass")["items"]}
    missing = {"platform-critical", "batch-high", "batch-low"} - pcs
    if missing:
        problems.append(f"missing PriorityClasses {sorted(missing)}")
    return not problems, "; ".join(
        problems
    ) or "quotas, LimitRanges, PriorityClasses present"


def c_rbac_isolation():
    def can(verb, res, ns):
        return (
            run(
                [
                    "kubectl",
                    "auth",
                    "can-i",
                    verb,
                    res,
                    "-n",
                    ns,
                    "--as=verify-user",
                    "--as-group=team-a-dev",
                ]
            )[1]
            .strip()
            .lower()
        )

    a, b = can("create", "deployments", "team-a"), can("get", "pods", "team-b")
    ok = a == "yes" and b == "no"
    return ok, f"team-a create deployments={a}, team-b get pods={b}"


# ---------------------------------------------------------------- Day 6: S7, S8
def c_sparkpi_completed():
    try:
        apps = kjson("get", "sparkapplications", "-A")["items"]
    except RuntimeError as e:
        return False, str(e)
    done = [
        a["metadata"]["name"]
        for a in apps
        if a.get("status", {}).get("applicationState", {}).get("state") == "COMPLETED"
    ]
    return bool(
        done
    ), f"COMPLETED: {done}" if done else "no SparkApplication in COMPLETED state"


def c_pytest_ingest():
    if not any((ROOT / "jobs" / "ingest").rglob("test_*.py")):
        return False, "no tests in jobs/ingest yet"
    rc, out = run(["pytest", "-q", "jobs/ingest"], timeout=300)
    return rc == 0, short(out.splitlines()[-1] if out else "")


# ---------------------------------------------------------------- Week 2 repo checks
def c_helm_requires_digest():
    chart = ROOT / "charts" / "spark-job"
    if not (chart / "Chart.yaml").exists():
        return False, "charts/spark-job/Chart.yaml not created yet"
    rc, _ = run(["helm", "template", str(chart), "--set", "image.digest="])
    return (
        rc != 0,
        "helm template fails without image.digest"
        if rc != 0
        else "rendered WITHOUT image.digest",
    )


def c_kustomize_overlays_differ():
    outs = []
    for env in ("dev", "prod"):
        rc, out = run(["kubectl", "kustomize", f"gitops/overlays/{env}"])
        if rc != 0:
            return False, f"overlays/{env}: {short(out, 80)}"
        outs.append(out)
    return outs[0] != outs[1] and "schedule" in outs[
        0
    ], "dev and prod render differently" if outs[0] != outs[
        1
    ] else "dev and prod render identically"


# ---------------------------------------------------------------- registry
CHECKS = [
    ("Layout, README.md, notes/log.md", c_layout),
    ("Pre-commit installed", c_precommit_installed),
    ("Makefile targets: lint, test, plan, kubeconfig", c_makefile),
    ("Push to GitHub", c_github_protected),
    ("`pre-commit run --all-files` passes on a clean clone", c_precommit_clean_clone),
    ("Committing a fake AWS key is blocked by gitleaks", c_gitleaks_blocks),
    ("Agent labels `node-role/data=true`", c_node_labels_taint),
    ("Namespaces platform, data, monitoring, chaos, team-a, team-b", c_namespaces),
    ("PSA baseline on all namespaces", c_psa_labels),
    ("`kubectl get nodes -o wide`: all Ready", c_nodes_ready_labeled),
    ("A privileged pod in team-a is rejected by PSA", c_psa_rejects_privileged),
    ("Cluster `pg-lake` in data", c_pg_lake_cluster),
    ("Services pg-lake-rw / pg-lake-ro", c_pg_lake_services),
    ("Default-deny (ingress + egress) in data, team-a, team-b", c_default_deny),
    ("Every UI loads over HTTPS by hostname", c_uis_https),
    ("`git grep -i password` finds no plaintext values", c_no_plaintext_passwords),
    ("A 5-CPU job in team-a is rejected by quota", c_quota_rejects),
    ("Quotas team-a/team-b", c_quotas_limitranges_pcs),
    ("`kubectl auth can-i` as team-a-dev", c_rbac_isolation),
    ("SparkPi SparkApplication shows COMPLETED", c_sparkpi_completed),
    ("`pytest jobs/ingest` passes", c_pytest_ingest),
    ("`helm template` fails without image.digest", c_helm_requires_digest),
    ("`kustomize build` dev vs prod", c_kustomize_overlays_differ),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dry-run", action="store_true", help="report only; don't edit tracker.md"
    )
    ap.add_argument("--all", action="store_true", help="include days after today")
    ap.add_argument(
        "--recheck", action="store_true", help="re-run ticked items, report regressions"
    )
    ap.add_argument("--date", type=dt.date.fromisoformat, default=dt.date.today())
    a = ap.parse_args()

    lines = TRACKER.read_text().splitlines(keepends=True)
    day = None
    targets = []  # (line_index, ticked, text, func)
    for i, line in enumerate(lines):
        if m := DAY_RE.match(line):
            day = dt.date.fromisoformat(m.group(1))
        if not (m := BOX_RE.match(line.rstrip("\n"))):
            continue
        if day and day > a.date and not a.all:
            continue
        hits = [f for key, f in CHECKS if key in m.group(2)]
        if hits:
            targets.append((i, m.group(1).lower() == "x", m.group(2), hits[0]))

    ticked_now, passed, failed, regress = [], 0, 0, 0
    for i, ticked, text, fn in targets:
        if ticked and not a.recheck:
            continue
        try:
            ok, detail = fn()
        except Exception as e:  # noqa: BLE001
            ok, detail = False, f"error: {e}"
        label = short(re.sub(r"[`*✅]", "", text), 70)
        if ok:
            passed += 1
            print(f"  PASS  {label}\n        {detail}")
            if not ticked:
                lines[i] = lines[i].replace("- [ ]", "- [x]", 1)
                ticked_now.append(label)
        else:
            failed += 1
            tag = "REGRESSED" if ticked else "FAIL"
            regress += ticked
            print(f"  {tag:<5} {label}\n        {detail}")

    if ticked_now and not a.dry_run:
        TRACKER.write_text("".join(lines))
    print(
        f"\n{passed} passed · {failed} failing · "
        + (
            f"{len(ticked_now)} newly ticked"
            + (" (dry run, not saved)" if a.dry_run else "")
        )
    )
    if regress:
        print(
            f"{regress} previously ticked item(s) now fail. Untick them by hand if the regression is real."
        )
    print(
        "Items without an automated check (playbooks, drills, logs, preemption, backups) are ticked by hand."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
