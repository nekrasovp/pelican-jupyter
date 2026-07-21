"""Fail closed when the hosted workflow exceeds the PLUGIN-003 trust policy."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

WORKFLOW = Path(".github/workflows/test.yml")
FULL_COMMIT = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_PYTHONS = {"3.10", "3.11", "3.12", "3.13"}
ALLOWED_ACTIONS = {"actions/checkout", "actions/setup-python"}


def _fail(message: str) -> None:
    raise SystemExit(f"workflow policy failure: {message}")


def main() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")
    workflow = yaml.safe_load(raw)
    if workflow.get("permissions") != {"contents": "read"}:
        _fail("top-level permissions must be exactly contents: read")

    forbidden_text = (
        "pull_request_target",
        "secrets",
        "id-token: write",
        "contents: write",
        "packages: write",
        "actions/upload-artifact",
        "codecov/",
        "git push",
        "gh pr",
        "twine upload",
        "curl ",
        "wget ",
    )
    for token in forbidden_text:
        if token in raw:
            _fail(f"forbidden workflow token {token!r}")

    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        _fail("workflow has no jobs")

    actions: list[tuple[str, dict]] = []
    for job_name, job in jobs.items():
        if "permissions" in job:
            _fail(f"job {job_name!r} overrides permissions")
        for step in job.get("steps", []):
            use = step.get("uses")
            if use is not None:
                actions.append((use, step.get("with", {})))

    if not actions:
        _fail("workflow uses no actions")
    for use, inputs in actions:
        try:
            action, revision = use.rsplit("@", 1)
        except ValueError:
            _fail(f"action is not pinned: {use!r}")
        if action not in ALLOWED_ACTIONS:
            _fail(f"action is outside the allowlist: {action!r}")
        if not FULL_COMMIT.fullmatch(revision):
            _fail(f"action is not pinned to a full commit: {use!r}")
        if (
            action == "actions/checkout"
            and inputs.get("persist-credentials") is not False
        ):
            _fail("every checkout must set persist-credentials: false")

    for version in REQUIRED_PYTHONS:
        if version not in raw:
            _fail(f"Python {version} is missing from the hosted matrix")
    pelican_constraint = Path("ci/constraints-pelican412.txt").read_text(
        encoding="utf-8"
    )
    if (
        "constraints-pelican412.txt" not in raw
        or "pelican==4.12.0" not in pelican_constraint.casefold()
    ):
        _fail("Pelican 4.12 is not explicitly exercised")
    if "requirements-min.txt" not in raw:
        _fail("the declared-minimum committed input is not exercised")
    if "requirements-dev.lock.txt" not in raw:
        _fail("the current committed lock is not exercised")
    if "requirements.txt" not in raw:
        _fail("the latest-compatible committed input is not exercised")
    if "cac7d59b7a691ebdedea17f5978ce24693830bf8" not in raw:
        _fail("external integration is not pinned to the contracted commit")

    print(
        "workflow policy passed: contents:read, no secrets/write actions, "
        f"{len(actions)} actions pinned"
    )


if __name__ == "__main__":
    main()
