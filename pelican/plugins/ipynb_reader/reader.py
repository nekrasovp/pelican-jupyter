"""Current Pelican 4 reader for direct ``.ipynb + .nbdata`` articles."""

from __future__ import annotations

import ast
import shutil
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any, TypedDict

import nbformat
from markdown import Markdown
from pelican.contents import Category, Tag
from pelican.readers import BaseReader, MarkdownReader

from .conversion import HTML_CONTRACT_VERSION, convert_notebook_fragment
from .errors import (
    MetadataDiscoveryError,
    MetadataParsingError,
    MetadataValidationError,
    NotebookConversionError,
    NotebookCopyError,
    NotebookParsingError,
)


class NotebookMetadata(TypedDict, total=False):
    """Stable reader-owned metadata available to Pelican articles/themes."""

    title: str
    date: Any
    slug: str
    tags: list[Tag]
    category: Category
    summary: str
    jupyter_notebook: bool
    notebook_html_contract: str
    nb_path: str
    subcells: tuple[int, int | None]


class _SummaryParser(HTMLParser):
    _SKIP_TAGS = {"code", "pre", "script", "style"}
    _STOP_CLASSES = {"input", "input_area", "output", "output_area", "output_wrapper"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self.stopped = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.stopped:
            return
        classes = next((value for name, value in attrs if name == "class"), "") or ""
        if set(classes.split()) & self._STOP_CLASSES:
            self.stopped = True
            return
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if not self.stopped and tag in self._SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.stopped and not self._skip_depth and data != "¶":
            self.parts.append(data)


def _generated_summary(fragment: str, settings: dict[str, Any]) -> str:
    try:
        limit = int(settings["SUMMARY_MAX_LENGTH"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("SUMMARY_MAX_LENGTH must be a positive integer") from exc
    if limit <= 0:
        raise ValueError("SUMMARY_MAX_LENGTH must be a positive integer")

    parser = _SummaryParser()
    parser.feed(fragment)
    parser.close()
    words = " ".join(parser.parts).split()
    summary = " ".join(words[:limit])
    if len(words) > limit:
        summary += str(settings.get("SUMMARY_END_SUFFIX", "…"))
    return summary


def _metadata_values(raw_metadata: dict[str, list[str]], name: str) -> list[str]:
    return next(
        (values for key, values in raw_metadata.items() if key.lower() == name),
        [],
    )


class IPYNBReader(BaseReader):
    """Static direct-notebook reader; cells are never executed."""

    enabled = True
    file_extensions = ["ipynb"]

    def _read_metadata(self, source_path: Path) -> NotebookMetadata:
        metadata_path = source_path.with_suffix(".nbdata")
        if not metadata_path.is_file():
            raise MetadataDiscoveryError(
                source_path,
                "missing_metadata",
                f"adjacent metadata file not found: {metadata_path}",
                cause_type="MissingMetadata",
            )

        try:
            markdown_settings = deepcopy(self.settings.get("MARKDOWN", {}))
            extensions = list(markdown_settings.get("extensions", ()))
            if "markdown.extensions.meta" not in extensions:
                extensions.append("markdown.extensions.meta")
            markdown_settings["extensions"] = extensions
            parser = Markdown(**markdown_settings)
            source_text = metadata_path.read_text(encoding="utf-8")
            residual_content = parser.convert(source_text)
            raw_metadata = getattr(parser, "Meta", {})
        except Exception as exc:
            error = MetadataParsingError.from_cause(
                source_path, "malformed_metadata", exc
            )
            raise error from exc

        if residual_content.strip():
            raise MetadataParsingError(
                source_path,
                "malformed_metadata",
                f"{metadata_path} contains non-metadata content",
                cause_type="MalformedMetadata",
            )

        title_values = _metadata_values(raw_metadata, "title")
        date_values = _metadata_values(raw_metadata, "date")
        if len(title_values) != 1 or not title_values[0].strip():
            raise MetadataValidationError(
                source_path,
                "missing_title",
                "metadata field 'title' is required and must be non-empty",
                cause_type="MissingTitle",
            )
        if len(date_values) != 1 or not date_values[0].strip():
            raise MetadataValidationError(
                source_path,
                "missing_date",
                "metadata field 'date' is required and must be non-empty",
                cause_type="MissingDate",
            )

        try:
            _ignored, normalized = MarkdownReader(deepcopy(self.settings)).read(
                str(metadata_path)
            )
        except Exception as exc:
            error = MetadataValidationError.from_cause(
                source_path, "invalid_metadata", exc
            )
            raise error from exc

        normalized["jupyter_notebook"] = self.process_metadata("jupyter_notebook", True)
        normalized["notebook_html_contract"] = self.process_metadata(
            "notebook_html_contract", HTML_CONTRACT_VERSION
        )
        return normalized

    def _subcells(
        self, source_path: Path, metadata: NotebookMetadata
    ) -> tuple[int, int | None]:
        raw = metadata.get("subcells")
        if raw is None:
            return 0, None
        try:
            parsed = ast.literal_eval(raw) if isinstance(raw, str) else raw
            if not isinstance(parsed, (tuple, list)) or len(parsed) != 2:
                raise ValueError("Subcells must be a two-item tuple or list")
            start, end = parsed
            if isinstance(start, bool) or not isinstance(start, int) or start < 0:
                raise ValueError("Subcells start must be a non-negative integer")
            if end is not None and (
                isinstance(end, bool) or not isinstance(end, int) or end < start
            ):
                raise ValueError("Subcells end must be None or an integer >= start")
        except (SyntaxError, ValueError, TypeError) as exc:
            error = MetadataValidationError.from_cause(
                source_path, "invalid_subcells", exc
            )
            raise error from exc

        result = (start, end)
        metadata["subcells"] = self.process_metadata("subcells", result)
        return result

    def _copy_notebook(self, source_path: Path, metadata: NotebookMetadata) -> None:
        save_as = self.settings.get("IPYNB_NB_SAVE_AS")
        if not save_as:
            return
        try:
            public_path = PurePosixPath(str(save_as).format(**metadata))
            if public_path.is_absolute() or ".." in public_path.parts:
                raise ValueError("IPYNB_NB_SAVE_AS must be a safe relative path")
            output_root = Path(self.settings["OUTPUT_PATH"]).resolve()
            destination = output_root.joinpath(*public_path.parts).resolve()
            if not destination.is_relative_to(output_root):
                raise ValueError("IPYNB_NB_SAVE_AS escapes OUTPUT_PATH")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, destination)
        except Exception as exc:
            error = NotebookCopyError.from_cause(source_path, "copy_failed", exc)
            raise error from exc
        metadata["nb_path"] = self.process_metadata("nb_path", public_path.as_posix())

    def read(self, source_path: str) -> tuple[str, NotebookMetadata]:
        source = Path(source_path)
        metadata = self._read_metadata(source)
        start, end = self._subcells(source, metadata)

        try:
            notebook = nbformat.read(source, as_version=4)
            nbformat.validate(notebook)
        except Exception as exc:
            error = NotebookParsingError.from_cause(source, "malformed_notebook", exc)
            raise error from exc

        try:
            preprocessors = self.settings.get("IPYNB_PREPROCESSORS", ())
            content = convert_notebook_fragment(
                notebook,
                start=start,
                end=end,
                preprocessors=preprocessors,
            )
        except Exception as exc:
            error = NotebookConversionError.from_cause(source, "conversion_failed", exc)
            raise error from exc

        if "summary" not in metadata:
            try:
                metadata["summary"] = self.process_metadata(
                    "summary", _generated_summary(content, self.settings)
                )
            except Exception as exc:
                error = MetadataValidationError.from_cause(
                    source, "invalid_summary_settings", exc
                )
                raise error from exc

        self._copy_notebook(source, metadata)
        return content, metadata


# Historical class spelling remains an alias, never a second implementation.
IPythonNB = IPYNBReader
