"""Inspect one RC wheel/sdist pair and smoke-test clean artifact installs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path
from typing import Sequence


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess:
    environment = {
        key: value for key, value in os.environ.items() if key != "PYTHONPATH"
    }
    return subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def _checked(command: list[str], *, cwd: Path) -> str:
    result = _run(command, cwd=cwd)
    if result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"{result.stdout}{result.stderr}"
        )
    return result.stdout + result.stderr


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _wheel_metadata(path: Path) -> tuple[list[str], str]:
    with zipfile.ZipFile(path) as archive:
        names = sorted(archive.namelist())
        metadata_name = next(
            name for name in names if name.endswith(".dist-info/METADATA")
        )
        metadata = archive.read(metadata_name).decode("utf-8")
    return names, metadata


def _sdist_names(path: Path) -> list[str]:
    with tarfile.open(path, "r:gz") as archive:
        return sorted(member.name for member in archive.getmembers() if member.isfile())


def _require_suffix(names: list[str], suffix: str, artifact: str) -> None:
    if not any(name.endswith(suffix) for name in names):
        raise RuntimeError(f"{artifact} is missing required path suffix {suffix!r}")


def _inspect(wheel: Path, sdist: Path) -> dict:
    wheel_names, metadata_text = _wheel_metadata(wheel)
    sdist_names = _sdist_names(sdist)
    metadata = Parser().parsestr(metadata_text)

    for suffix in (
        "pelican/plugins/ipynb_reader/publication.py",
        ".dist-info/licenses/LICENSE.txt",
        ".data/data/share/doc/pelican-jupyter/PROVENANCE.md",
    ):
        _require_suffix(wheel_names, suffix, "wheel")
    if any(
        "/tests/" in name
        or name.endswith((".ipynb", ".nbdata"))
        or "/examples/" in name
        for name in wheel_names
    ):
        raise RuntimeError(
            "wheel must not contain tests, notebooks, metadata fixtures, or examples"
        )

    for suffix in (
        "/LICENSE.txt",
        "/docs/FIRST_RELEASE_CONTRACT.md",
        "/docs/PROVENANCE.md",
        "/examples/visual-review/content/contract-v1.ipynb",
        "/examples/visual-review/content/contract-v1.nbdata",
        "/pelican/plugins/ipynb_reader/publication.py",
        "/pelican_jupyter/tests/fixtures/nbconvert-basic.v1/representative.fragment.html",
    ):
        _require_suffix(sdist_names, suffix, "sdist")

    if metadata["License"] != "Apache-2.0":
        raise RuntimeError("wheel metadata does not declare Apache-2.0")
    if metadata["Requires-Python"] != ">=3.10,<3.14":
        raise RuntimeError("wheel metadata does not contain the declared Python policy")
    project_urls = metadata.get_all("Project-URL", [])
    if not any(value.startswith("Upstream,") for value in project_urls):
        raise RuntimeError("wheel metadata is missing upstream provenance")

    forbidden = ("/Users/", "Documents/Codex", "nekrasovp.ru")
    if any(token in metadata_text for token in forbidden):
        raise RuntimeError(
            "wheel metadata contains a local path or personal site domain"
        )

    return {
        "sdist": {
            "file_count": len(sdist_names),
            "filename": sdist.name,
            "files": sdist_names,
            "sha256": _sha256(sdist),
        },
        "version": metadata["Version"],
        "wheel": {
            "file_count": len(wheel_names),
            "filename": wheel.name,
            "files": wheel_names,
            "sha256": _sha256(wheel),
        },
    }


def _write_example(root: Path) -> None:
    content = root / "content"
    content.mkdir(parents=True)
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "id": "artifact-markdown",
                "metadata": {},
                "source": ["Artifact-only **example**."],
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "id": "artifact-code",
                "metadata": {},
                "outputs": [
                    {
                        "name": "stdout",
                        "output_type": "stream",
                        "text": ["ARTIFACT_COMMITTED_OUTPUT\\n"],
                    }
                ],
                "source": ["raise AssertionError('must not execute')"],
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Definitely not installed",
                "language": "python",
                "name": "definitely-not-installed",
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (content / "artifact.ipynb").write_text(
        json.dumps(notebook, indent=1) + "\n", encoding="utf-8"
    )
    (content / "artifact.nbdata").write_text(
        "Title: Artifact example\n"
        "Date: 2026-07-22\n"
        "Slug: artifact-example\n"
        "Summary: Clean artifact example.\n",
        encoding="utf-8",
    )
    (root / "pelicanconf.py").write_text(
        "AUTHOR_FEED_ATOM = None\n"
        "AUTHOR_FEED_RSS = None\n"
        "CATEGORY_FEED_ATOM = None\n"
        "FEED_ALL_ATOM = None\n"
        "MARKUP = ('ipynb',)\n"
        "PLUGINS = ['pelican.plugins.ipynb_reader']\n"
        "SITEURL = ''\n"
        "TIMEZONE = 'UTC'\n"
        "TRANSLATION_FEED_ATOM = None\n",
        encoding="utf-8",
    )


def _clean_install_smoke(
    *,
    label: str,
    artifact: Path,
    python: str,
    requirements: Path,
    work_root: Path,
    expected_version: str,
) -> dict:
    root = work_root / label
    environment = root / "venv"
    project = root / "example"
    root.mkdir()
    _checked([python, "-m", "venv", str(environment)], cwd=root)
    executable = environment / "bin" / "python"
    if sys.platform == "win32":
        executable = environment / "Scripts" / "python.exe"
    _checked(
        [
            str(executable),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-r",
            str(requirements),
        ],
        cwd=root,
    )
    _checked(
        [
            str(executable),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-deps",
            str(artifact),
        ],
        cwd=root,
    )
    _checked([str(executable), "-m", "pip", "check"], cwd=root)
    _write_example(project)
    import_probe = _checked(
        [
            str(executable),
            "-I",
            "-c",
            (
                "from importlib.metadata import version; "
                "from pathlib import Path; "
                "import pelican.plugins.ipynb_reader as reader; "
                f"assert version('pelican-jupyter') == {expected_version!r}; "
                "assert 'site-packages' in Path(reader.__file__).as_posix(); "
                "print(reader.HTML_CONTRACT_VERSION)"
            ),
        ],
        cwd=project,
    )
    build = _checked(
        [
            str(executable),
            "-I",
            "-m",
            "pelican",
            "content",
            "--settings",
            "pelicanconf.py",
            "--output",
            "output",
            "--delete-output-directory",
            "--fatal",
            "errors",
        ],
        cwd=project,
    )
    html = (project / "output" / "artifact-example.html").read_text(encoding="utf-8")
    required = ("ARTIFACT_COMMITTED_OUTPUT", "cell", "input_area")
    if not all(token in html for token in required) or "jp-" in html.casefold():
        raise RuntimeError(f"{label} example output violates the fragment contract")
    processed = re.search(r"Done: Processed (\d+) articles?", build)
    if not processed or int(processed.group(1)) != 1:
        raise RuntimeError(f"{label} example did not publish exactly one article")
    return {
        "artifact": artifact.name,
        "contract": import_probe.strip(),
        "example_articles": 1,
        "import_from_site_packages": True,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--dist", type=Path, required=True)
    result.add_argument("--requirements", type=Path, required=True)
    result.add_argument("--work-root", type=Path, required=True)
    result.add_argument("--report-out", type=Path, required=True)
    result.add_argument("--python", default=sys.executable)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        wheels = sorted(args.dist.resolve().glob("*.whl"))
        sdists = sorted(args.dist.resolve().glob("*.tar.gz"))
        if len(wheels) != 1 or len(sdists) != 1:
            raise RuntimeError("dist must contain exactly one wheel and one sdist")
        if args.work_root.exists():
            raise RuntimeError("work-root must not already exist")
        args.work_root.mkdir(parents=True)
        report = _inspect(wheels[0], sdists[0])
        report["clean_installs"] = [
            _clean_install_smoke(
                label=label,
                artifact=artifact,
                python=args.python,
                requirements=args.requirements.resolve(),
                work_root=args.work_root,
                expected_version=report["version"],
            )
            for label, artifact in (("wheel", wheels[0]), ("sdist", sdists[0]))
        ]
        report["contract"] = "pelican-ipynb-artifacts.v1"
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except Exception as error:
        print(f"artifact verification failed: {error}", file=sys.stderr)
        return 1
    print(
        f"artifact verification passed: {report['wheel']['filename']} and "
        f"{report['sdist']['filename']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
