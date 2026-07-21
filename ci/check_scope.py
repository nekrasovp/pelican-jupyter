"""Reject personal-site material and local paths from package-owned fixtures."""

from __future__ import annotations

import subprocess
from pathlib import Path

SCOPED_ROOTS = ("pelican/", "pelican_jupyter/", "examples/")
FORBIDDEN_TEXT = ("/Users/", "Documents/Codex", "nekrasovp.ru")


def _candidate_paths() -> list[Path]:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            *SCOPED_ROOTS,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return [Path(value) for value in result.stdout.splitlines()]


def main() -> None:
    errors: list[str] = []
    notebooks: list[Path] = []
    paths = _candidate_paths()
    for path in paths:
        if path.suffix == ".ipynb":
            notebooks.append(path)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for token in FORBIDDEN_TEXT:
            if token in text:
                errors.append(f"{path}: contains forbidden token {token!r}")

    allowed_notebook_roots = (
        "examples/visual-review/content/",
        "pelican_jupyter/tests/fixtures/",
        "pelican_jupyter/tests/pelican/",
    )
    for path in notebooks:
        if not path.as_posix().startswith(allowed_notebook_roots):
            errors.append(f"{path}: notebook is outside generic fixture roots")

    if errors:
        raise SystemExit("scope/privacy scan failed:\n" + "\n".join(errors))
    print(
        f"scope/privacy scan passed: {len(paths)} files, "
        f"{len(notebooks)} generic notebooks"
    )


if __name__ == "__main__":
    main()
