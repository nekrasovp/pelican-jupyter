"""Versioned static conversion boundary for notebook HTML fragments."""

from __future__ import annotations

from copy import deepcopy
from re import IGNORECASE, search
from typing import Any, Iterable

from nbconvert import HTMLExporter

HTML_CONTRACT_VERSION = "nbconvert-basic.v1"


def _preprocessor_names(preprocessor: Any) -> set[str]:
    if isinstance(preprocessor, str):
        return {preprocessor}
    candidate = preprocessor if isinstance(preprocessor, type) else type(preprocessor)
    return {
        f"{item.__module__}.{item.__name__}"
        for item in getattr(candidate, "__mro__", (candidate,))
    }


def validate_static_preprocessors(preprocessors: Iterable[Any]) -> tuple[Any, ...]:
    """Reject nbconvert's code-execution preprocessor and return an immutable list."""

    validated = tuple(preprocessors)
    for preprocessor in validated:
        names = _preprocessor_names(preprocessor)
        if any(name.rsplit(".", 1)[-1] == "ExecutePreprocessor" for name in names):
            raise ValueError("IPYNB_PREPROCESSORS must not contain ExecutePreprocessor")
    return validated


def _validate_fragment(fragment: str, has_cells: bool, has_code: bool) -> None:
    if search(r"<\s*/?\s*(?:html|body)\b", fragment, flags=IGNORECASE):
        raise ValueError("HTML fragment contains a nested html/body document wrapper")
    if search(r'(?:class|id)\s*=\s*["\'][^"\']*\bjp-', fragment, flags=IGNORECASE):
        raise ValueError("HTML fragment contains unsupported jp-* contract markup")
    if has_cells and not search(r'class\s*=\s*["\'][^"\']*\bcell\b', fragment):
        raise ValueError("HTML fragment does not contain the required cell contract")
    if has_code and not search(r'class\s*=\s*["\'][^"\']*\binput_area\b', fragment):
        raise ValueError(
            "HTML fragment does not contain the required input_area contract"
        )


def convert_notebook_fragment(
    notebook: Any,
    *,
    start: int = 0,
    end: int | None = None,
    preprocessors: Iterable[Any] = (),
) -> str:
    """Convert committed notebook state without executing it.

    ``HTMLExporter(template_name="basic")`` is the complete default template
    selection for contract version ``nbconvert-basic.v1``.
    """

    selected = deepcopy(notebook)
    selected.cells = selected.cells[start:end]
    static_preprocessors = validate_static_preprocessors(preprocessors)

    exporter = HTMLExporter(template_name="basic")
    for preprocessor in static_preprocessors:
        exporter.register_preprocessor(preprocessor, enabled=True)

    fragment, _resources = exporter.from_notebook_node(selected)
    _validate_fragment(
        fragment,
        has_cells=bool(selected.cells),
        has_code=any(cell.cell_type == "code" for cell in selected.cells),
    )
    return fragment
