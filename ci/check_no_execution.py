"""Statically enforce the owned reader's narrow no-execution boundary."""

from __future__ import annotations

import ast
from pathlib import Path

RUNTIME_ROOT = Path("pelican/plugins/ipynb_reader")
FORBIDDEN_MODULES = {"jupyter_client", "nbclient"}
FORBIDDEN_CALLS = {"execute", "execute_cell", "start_kernel"}


def _module_root(name: str) -> str:
    return name.split(".", 1)[0]


def main() -> None:
    errors: list[str] = []
    paths = sorted(RUNTIME_ROOT.glob("*.py"))
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _module_root(alias.name) in FORBIDDEN_MODULES:
                        errors.append(f"{path}:{node.lineno}: imports {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module and _module_root(node.module) in FORBIDDEN_MODULES:
                    errors.append(f"{path}:{node.lineno}: imports {node.module}")
            elif isinstance(node, ast.Call):
                name = None
                if isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                elif isinstance(node.func, ast.Name):
                    name = node.func.id
                if name in FORBIDDEN_CALLS:
                    errors.append(f"{path}:{node.lineno}: calls {name}")
    if errors:
        raise SystemExit(
            "owned reader may not execute notebooks:\n" + "\n".join(errors)
        )
    print(f"no-execution source scan passed: {len(paths)} runtime modules")


if __name__ == "__main__":
    main()
