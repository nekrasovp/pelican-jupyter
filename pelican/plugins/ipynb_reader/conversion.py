"""Versioned static conversion boundary for notebook HTML fragments."""

from __future__ import annotations

from copy import deepcopy
from html.parser import HTMLParser
from re import IGNORECASE, search
from typing import Any, Iterable

from nbconvert import HTMLExporter

HTML_CONTRACT_VERSION = "nbconvert-basic.v1"


class _FragmentAttributes(HTMLParser):
    """Collect exact whitespace-delimited class and id tokens."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.class_tokens: set[str] = set()
        self.id_tokens: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del tag
        for name, value in attrs:
            if value is None:
                continue
            if name.casefold() == "class":
                self.class_tokens.update(value.split())
            elif name.casefold() == "id":
                self.id_tokens.update(value.split())

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def _fragment_attributes(fragment: str) -> _FragmentAttributes:
    attributes = _FragmentAttributes()
    attributes.feed(fragment)
    attributes.close()
    return attributes


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
    attributes = _fragment_attributes(fragment)
    if any(
        token.casefold().startswith("jp-")
        for token in attributes.class_tokens | attributes.id_tokens
    ):
        raise ValueError("HTML fragment contains unsupported jp-* contract markup")
    if has_cells and "cell" not in attributes.class_tokens:
        raise ValueError("HTML fragment does not contain the required cell contract")
    if has_code and "input_area" not in attributes.class_tokens:
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
