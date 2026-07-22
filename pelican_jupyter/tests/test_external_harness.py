from pathlib import Path
from types import SimpleNamespace

import pytest

from ci.external_corpus import _gate_command, _resolve_python


def test_relative_python_is_resolved_from_invocation_directory(tmp_path, monkeypatch):
    invocation_root = tmp_path / "invocation"
    executable = invocation_root / "external-site" / ".venv" / "bin" / "python"
    executable.parent.mkdir(parents=True)
    executable.write_text("", encoding="utf-8")
    subprocess_root = tmp_path / "subprocess-work"
    subprocess_root.mkdir()

    monkeypatch.chdir(invocation_root)
    resolved = _resolve_python("external-site/.venv/bin/python")
    monkeypatch.chdir(subprocess_root)

    assert Path(resolved).is_absolute()
    assert Path(resolved) == executable.resolve()


def test_missing_python_is_a_typed_harness_failure(tmp_path):
    with pytest.raises(RuntimeError, match="Python executable is unavailable"):
        _resolve_python("missing/bin/python", invocation_root=tmp_path)


def test_python_symlink_is_kept_to_preserve_virtual_environment(tmp_path):
    target = tmp_path / "python-target"
    target.write_text("", encoding="utf-8")
    virtualenv_python = tmp_path / ".venv" / "bin" / "python"
    virtualenv_python.parent.mkdir(parents=True)
    virtualenv_python.symlink_to(target)

    resolved = _resolve_python(".venv/bin/python", invocation_root=tmp_path)

    assert Path(resolved) == virtualenv_python.absolute()
    assert Path(resolved).is_symlink()


def test_gate_command_uses_normalized_paths_after_working_directory_change(
    tmp_path, monkeypatch
):
    invocation_root = tmp_path / "invocation"
    invocation_root.mkdir()
    args = SimpleNamespace(
        python=str((invocation_root / ".venv" / "bin" / "python").absolute()),
        expected_manifest=(invocation_root / "expected.tsv").absolute(),
        baseline_metadata=(invocation_root / "baseline.json").absolute(),
        site_root=(invocation_root / "external-site").absolute(),
        external_commit="0" * 40,
        expected_articles=46,
        expected_notebooks=11,
        expected_missing_alt=57,
        expected_empty_alt=2,
        timezone="UTC",
    )
    subprocess_root = tmp_path / "subprocess-work"
    subprocess_root.mkdir()
    monkeypatch.chdir(subprocess_root)

    command = _gate_command(
        args, (subprocess_root / "output").absolute(), subprocess_root / "evidence"
    )

    assert command[0] == args.python
    assert command[command.index("--content-root") + 1] == str(
        args.site_root / "content"
    )
