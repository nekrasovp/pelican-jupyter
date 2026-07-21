"""Independent expected-source and expected-route publication verification."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any, Sequence

import nbformat
from pelican.settings import read_settings

from .errors import NotebookPublicationError
from .reader import IPYNBReader


@dataclass(frozen=True)
class ExpectedArticle:
    """One expected publication supplied by a publisher-owned manifest."""

    route: str
    published_at: str
    language: str
    source: str
    title: str

    @property
    def is_notebook(self) -> bool:
        return self.source.casefold().endswith(".ipynb")


class _PlainText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


class _HTMLFacts(HTMLParser):
    """Collect stable metadata and content facts without theme-specific CSS."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.body_count = 0
        self.class_tokens: set[str] = set()
        self.empty_alt = 0
        self.html_count = 0
        self.html_lang: str | None = None
        self.id_tokens: set[str] = set()
        self.meta: dict[str, list[str]] = {}
        self.missing_alt = 0
        self.nbconvert_missing_alt = 0
        self.times: list[str] = []
        self.title_parts: list[str] = []
        self._entry_div_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.casefold(): value for name, value in attrs}
        classes = (values.get("class") or "").split()
        self.class_tokens.update(classes)
        self.id_tokens.update((values.get("id") or "").split())

        tag = tag.casefold()
        if tag == "html":
            self.html_count += 1
            self.html_lang = values.get("lang")
        elif tag == "body":
            self.body_count += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = values.get("property") or values.get("name")
            content = values.get("content")
            if key and content is not None:
                self.meta.setdefault(key.casefold(), []).append(content)
        elif tag == "time" and values.get("datetime"):
            self.times.append(values["datetime"] or "")

        if tag == "div":
            if self._entry_div_depth:
                self._entry_div_depth += 1
            elif "entry-content" in classes:
                self._entry_div_depth = 1
        elif tag == "img":
            if values.get("alt") == "No description has been provided for this image":
                self.nbconvert_missing_alt += 1
            if self._entry_div_depth:
                if "alt" not in values:
                    self.missing_alt += 1
                elif not (values.get("alt") or "").strip():
                    self.empty_alt += 1

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if tag == "title":
            self._in_title = False
        elif tag == "div" and self._entry_div_depth:
            self._entry_div_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return _normalize_text("".join(self.title_parts))


def _normalize_text(value: Any) -> str:
    return " ".join(str(value).split())


def _html_text(value: Any) -> str:
    parser = _PlainText()
    parser.feed(str(value))
    parser.close()
    return _normalize_text(" ".join(parser.parts))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _publication_error(
    source_path: str,
    category: str,
    message: str,
    cause_type: str,
) -> NotebookPublicationError:
    return NotebookPublicationError(
        source_path,
        category,
        message,
        cause_type=cause_type,
    )


def _load_expected(path: Path) -> list[ExpectedArticle]:
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            required = {"route", "published_at", "language", "source", "title"}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise ValueError(
                    "expected manifest must contain route, published_at, language, "
                    "source, and title columns"
                )
            rows = [
                ExpectedArticle(
                    route=row["route"].strip(),
                    published_at=row["published_at"].strip(),
                    language=row["language"].strip(),
                    source=row["source"].strip(),
                    title=row["title"].strip(),
                )
                for row in reader
            ]
    except NotebookPublicationError:
        raise
    except Exception as exc:
        error = _publication_error(
            str(path),
            "invalid_expected_manifest",
            str(exc),
            type(exc).__name__,
        )
        raise error from exc

    routes = [row.route for row in rows]
    sources = [row.source for row in rows]
    if len(routes) != len(set(routes)) or len(sources) != len(set(sources)):
        raise _publication_error(
            str(path),
            "duplicate_expectation",
            "expected routes and sources must be unique",
            "DuplicateExpectation",
        )
    for row in rows:
        source = PurePosixPath(row.source)
        if (
            not row.route.startswith("/")
            or not row.route.endswith(".html")
            or source.is_absolute()
            or ".." in source.parts
            or not row.published_at
            or not row.language
        ):
            raise _publication_error(
                row.source,
                "invalid_expectation",
                "route, source, publication date, or language is invalid",
                "InvalidExpectation",
            )
    return sorted(rows, key=lambda row: (row.route, row.source))


def _load_baseline(path: Path) -> dict[str, dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        pages = payload["pages"]
        result = {page["path"]: page for page in pages}
        if len(result) != len(pages):
            raise ValueError("baseline metadata contains duplicate paths")
        return result
    except Exception as exc:
        error = _publication_error(
            str(path),
            "invalid_baseline_metadata",
            str(exc),
            type(exc).__name__,
        )
        raise error from exc


def _notebook_modes(path: Path, fragment: str) -> set[str]:
    try:
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
    except Exception as exc:
        error = _publication_error(
            path.name,
            "invalid_expected_source",
            str(exc),
            type(exc).__name__,
        )
        raise error from exc

    modes: set[str] = set()
    for cell in notebook.cells:
        if cell.cell_type == "markdown":
            modes.add("markdown")
        elif cell.cell_type == "code":
            modes.add("code")
        for output in cell.get("outputs", ()):  # committed outputs only
            if output.output_type == "error":
                modes.add("error")
            data = output.get("data", {})
            if "image/png" in data:
                modes.update(("image", "png"))
            if "image/svg+xml" in data:
                modes.update(("image", "svg"))
            html = data.get("text/html", "")
            if isinstance(html, list):
                html = "".join(html)
            if "<table" in str(html).casefold():
                modes.add("table")
            elif html:
                modes.add("rich_html")
            if "application/javascript" in data:
                modes.add("javascript")
    rendered_markers = {
        "javascript": "output_javascript",
        "png": "data:image/png;base64",
        "rich_html": "output_html",
        "svg": "data:image/svg+xml;base64",
    }
    lowered = fragment.casefold()
    for mode, marker in rendered_markers.items():
        if mode in modes and marker.casefold() not in lowered:
            modes.discard(mode)
    if not modes.intersection(("png", "svg")):
        modes.discard("image")
    return modes


def _assert_equal(
    source: str,
    field: str,
    actual: Any,
    expected: Any,
) -> None:
    if actual != expected:
        raise _publication_error(
            source,
            "metadata_mismatch",
            f"{field}: expected={expected!r} actual={actual!r}",
            "MetadataMismatch",
        )


def _assert_fragment_contract(
    source: str,
    html: str,
    facts: _HTMLFacts,
    modes: set[str],
) -> None:
    tokens = facts.class_tokens | facts.id_tokens
    if facts.html_count != 1 or facts.body_count != 1:
        raise _publication_error(
            source,
            "nested_fragment_document",
            "published article must contain exactly one html and one body element",
            "NestedFragmentDocument",
        )
    if any(token.casefold().startswith("jp-") for token in tokens):
        raise _publication_error(
            source,
            "unsupported_fragment_markup",
            "published article contains jp-* class or id tokens",
            "UnsupportedFragmentMarkup",
        )
    required_tokens = {"cell"}
    if "code" in modes:
        required_tokens.add("input_area")
    missing = sorted(required_tokens - facts.class_tokens)
    if missing:
        raise _publication_error(
            source,
            "missing_fragment_token",
            f"published article is missing class tokens: {missing!r}",
            "MissingFragmentToken",
        )

    markers = {
        "png": "data:image/png;base64",
        "svg": "data:image/svg+xml;base64",
        "table": "<table",
        "error": "output_error",
        "rich_html": "output_html",
        "javascript": "output_javascript",
    }
    lowered = html.casefold()
    for mode, marker in markers.items():
        if mode in modes and marker.casefold() not in lowered:
            raise _publication_error(
                source,
                "missing_output_mode",
                f"published article is missing expected {mode} marker {marker!r}",
                "MissingOutputMode",
            )


def _normalization_settings(
    content_root: Path, output_root: Path, timezone: str
) -> dict[str, Any]:
    return read_settings(
        override={
            "AUTHOR_FEED_ATOM": None,
            "AUTHOR_FEED_RSS": None,
            "CATEGORY_FEED_ATOM": None,
            "FEED_ALL_ATOM": None,
            "OUTPUT_PATH": str(output_root),
            "PATH": str(content_root),
            "TIMEZONE": timezone,
            "TRANSLATION_FEED_ATOM": None,
        }
    )


def validate_publication(
    *,
    expected_manifest: Path,
    baseline_metadata: Path,
    content_root: Path,
    output_root: Path,
    external_commit: str,
    expected_articles: int,
    expected_notebooks: int,
    expected_missing_alt: int,
    expected_empty_alt: int,
    timezone: str,
) -> dict[str, Any]:
    """Validate publication output independently from Pelican's exit status."""

    expected = _load_expected(expected_manifest)
    baseline = _load_baseline(baseline_metadata)
    notebooks = [row for row in expected if row.is_notebook]
    markdown = [row for row in expected if not row.is_notebook]
    _assert_equal(
        str(expected_manifest), "article_count", len(expected), expected_articles
    )
    _assert_equal(
        str(expected_manifest),
        "notebook_count",
        len(notebooks),
        expected_notebooks,
    )

    settings = _normalization_settings(content_root, output_root, timezone)
    records: list[dict[str, Any]] = []
    mode_sources: dict[str, list[str]] = {}
    warning_records: list[dict[str, Any]] = []

    for row in expected:
        source_path = content_root.joinpath(*PurePosixPath(row.source).parts)
        route_path = output_root / row.route.lstrip("/")
        if not source_path.is_file():
            raise _publication_error(
                row.source,
                "missing_expected_source",
                "expected publication source is missing",
                "MissingExpectedSource",
            )
        if not route_path.is_file():
            raise _publication_error(
                row.source,
                "missing_expected_route",
                f"expected route is missing: {row.route}",
                "MissingExpectedRoute",
            )
        if row.route not in baseline:
            raise _publication_error(
                row.source,
                "missing_baseline_metadata",
                f"canonical baseline has no page for {row.route}",
                "MissingBaselineMetadata",
            )

        if not row.is_notebook:
            records.append(
                {
                    "route": row.route,
                    "source": row.source,
                    "source_kind": "markdown",
                }
            )
            continue

        baseline_page = baseline[row.route]
        _assert_equal(
            row.source, "source_kind", baseline_page.get("source_kind"), "notebook"
        )
        _assert_equal(
            row.source,
            "publication_date",
            baseline_page.get("publication_date"),
            row.published_at,
        )
        _assert_equal(row.source, "language", baseline_page.get("lang"), row.language)

        fragment, metadata = IPYNBReader(settings).read(str(source_path))

        reader_language = _normalize_text(metadata.get("lang", "")) or None
        if reader_language is not None:
            _assert_equal(
                row.source,
                "reader_language",
                reader_language,
                row.language,
            )
        normalized = {
            "category": _normalize_text(metadata.get("category", "")),
            "date": metadata["date"].date().isoformat(),
            "language": reader_language,
            "summary": _html_text(metadata.get("summary", "")),
            "tags": [_normalize_text(tag) for tag in metadata.get("tags", ())],
            "title": _normalize_text(metadata["title"]),
        }
        _assert_equal(row.source, "date", normalized["date"], row.published_at)
        _assert_equal(
            row.source,
            "jupyter_notebook",
            metadata.get("jupyter_notebook"),
            True,
        )
        _assert_equal(
            row.source,
            "notebook_html_contract",
            metadata.get("notebook_html_contract"),
            "nbconvert-basic.v1",
        )
        _assert_equal(
            row.source,
            "baseline_description",
            _normalize_text(baseline_page.get("description", "")),
            normalized["summary"],
        )

        html = route_path.read_text(encoding="utf-8")
        facts = _HTMLFacts()
        facts.feed(html)
        facts.close()
        fragment_facts = _HTMLFacts()
        fragment_facts.feed(fragment)
        fragment_facts.close()
        modes = _notebook_modes(source_path, fragment)
        _assert_fragment_contract(row.source, html, facts, modes)

        _assert_equal(row.source, "page_title", facts.title, baseline_page.get("title"))
        _assert_equal(
            row.source,
            "og:title",
            _normalize_text((facts.meta.get("og:title") or [""])[0]),
            normalized["title"],
        )
        _assert_equal(
            row.source,
            "description",
            _normalize_text((facts.meta.get("description") or [""])[0]),
            normalized["summary"],
        )
        published = (facts.meta.get("article:published_time") or [""])[0]
        _assert_equal(row.source, "published_date", published[:10], normalized["date"])
        _assert_equal(
            row.source,
            "category",
            _normalize_text((facts.meta.get("article:section") or [""])[0]),
            normalized["category"],
        )
        _assert_equal(
            row.source,
            "tags",
            [_normalize_text(tag) for tag in facts.meta.get("article:tag", ())],
            normalized["tags"],
        )

        for mode in sorted(modes):
            mode_sources.setdefault(mode, []).append(row.source)
        warning_records.append(
            {
                "empty_alt": facts.empty_alt,
                "missing_alt": fragment_facts.nbconvert_missing_alt,
                "source": row.source,
            }
        )
        records.append(
            {
                "content_class_sha256": _text_sha256(
                    "\n".join(sorted(facts.class_tokens))
                ),
                "content_modes": sorted(modes),
                "baseline_metadata": {
                    "language": baseline_page.get("lang"),
                    "page_title": baseline_page.get("title"),
                },
                "metadata": normalized,
                "publisher_target": {
                    "language": row.language,
                    "route_inventory_title": row.title,
                },
                "rendered_observation": {
                    "html_lang": facts.html_lang,
                    "page_title": facts.title,
                },
                "route": row.route,
                "source": row.source,
                "source_kind": "notebook",
                "source_sha256": _sha256(source_path),
            }
        )

    observed_missing_alt = sum(row["missing_alt"] for row in warning_records)
    observed_empty_alt = sum(row["empty_alt"] for row in warning_records)
    _assert_equal(
        str(expected_manifest),
        "nbconvert_missing_alt",
        observed_missing_alt,
        expected_missing_alt,
    )
    _assert_equal(
        str(expected_manifest),
        "empty_alt",
        observed_empty_alt,
        expected_empty_alt,
    )

    return {
        "contract": "pelican-ipynb-publication.v1",
        "counts": {
            "articles": len(expected),
            "markdown": len(markdown),
            "notebooks": len(notebooks),
        },
        "external_commit": external_commit,
        "output_modes": {
            mode: sorted(sources) for mode, sources in sorted(mode_sources.items())
        },
        "records": records,
        "warning_ledger": {
            "empty_alt": observed_empty_alt,
            "nbconvert_missing_alt": observed_missing_alt,
            "records": warning_records,
        },
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--expected-manifest", type=Path, required=True)
    result.add_argument("--baseline-metadata", type=Path, required=True)
    result.add_argument("--content-root", type=Path, required=True)
    result.add_argument("--output-root", type=Path, required=True)
    result.add_argument("--external-commit", required=True)
    result.add_argument("--expected-articles", type=int, required=True)
    result.add_argument("--expected-notebooks", type=int, required=True)
    result.add_argument("--expected-missing-alt", type=int, default=0)
    result.add_argument("--expected-empty-alt", type=int, default=0)
    result.add_argument("--timezone", default="UTC")
    result.add_argument("--evidence-out", type=Path)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        evidence = validate_publication(
            expected_manifest=args.expected_manifest.resolve(),
            baseline_metadata=args.baseline_metadata.resolve(),
            content_root=args.content_root.resolve(),
            output_root=args.output_root.resolve(),
            external_commit=args.external_commit,
            expected_articles=args.expected_articles,
            expected_notebooks=args.expected_notebooks,
            expected_missing_alt=args.expected_missing_alt,
            expected_empty_alt=args.expected_empty_alt,
            timezone=args.timezone,
        )
    except NotebookPublicationError as error:
        print(f"publication completeness failed: {error}", file=sys.stderr)
        return 1

    encoded = json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.evidence_out:
        args.evidence_out.parent.mkdir(parents=True, exist_ok=True)
        args.evidence_out.write_text(encoded, encoding="utf-8")
    print(
        "publication completeness passed: "
        f"{evidence['counts']['markdown']} Markdown + "
        f"{evidence['counts']['notebooks']} notebooks = "
        f"{evidence['counts']['articles']} articles"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
