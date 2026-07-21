from __future__ import annotations

import shutil

import nbformat
import pytest
from nbconvert.preprocessors import Preprocessor
from pelican.settings import read_settings

from pelican.plugins.ipynb_reader import (
    IPYNBReader,
    MetadataParsingError,
    MetadataValidationError,
    NotebookConversionError,
    NotebookCopyError,
    NotebookParsingError,
)


def _settings(tmp_path, **overrides):
    return read_settings(
        override={
            "OUTPUT_PATH": str(tmp_path / "output"),
            "PATH": str(tmp_path),
            "TIMEZONE": "UTC",
            **overrides,
        }
    )


def _write(tmp_path, cells, metadata="Title: Synthetic\nDate: 2026-07-21"):
    source = tmp_path / "synthetic.ipynb"
    nbformat.write(nbformat.v4.new_notebook(cells=cells), source)
    source.with_suffix(".nbdata").write_text(metadata, encoding="utf-8")
    return source


def test_explicit_summary_wins(tmp_path):
    source = _write(
        tmp_path,
        [nbformat.v4.new_markdown_cell("Generated text must not win.")],
        "Title: Synthetic\nDate: 2026-07-21\nSummary: Explicit *summary*.",
    )

    _content, metadata = IPYNBReader(_settings(tmp_path)).read(str(source))

    assert metadata["summary"] == "<p>Explicit <em>summary</em>.</p>"


def test_generated_summary_is_bounded_and_deterministic(tmp_path):
    source = _write(
        tmp_path,
        [nbformat.v4.new_markdown_cell("one two three four five")],
    )
    reader = IPYNBReader(
        _settings(tmp_path, SUMMARY_MAX_LENGTH=3, SUMMARY_END_SUFFIX="...")
    )

    first = reader.read(str(source))
    second = reader.read(str(source))

    assert first == second
    assert first[1]["summary"] == "one two three..."


def test_subcells_uses_validated_zero_based_half_open_slice(tmp_path):
    source = _write(
        tmp_path,
        [
            nbformat.v4.new_markdown_cell("excluded-zero"),
            nbformat.v4.new_markdown_cell("included-one"),
            nbformat.v4.new_code_cell("included_two = True"),
        ],
        "Title: Synthetic\nDate: 2026-07-21\nSubcells: (1, 3)",
    )

    content, metadata = IPYNBReader(_settings(tmp_path)).read(str(source))

    assert "excluded-zero" not in content
    assert "included-one" in content
    assert "included_two" in content
    assert metadata["subcells"] == (1, 3)


class AppendStaticMarker(Preprocessor):
    def preprocess_cell(self, cell, resources, index):
        if cell.cell_type == "markdown":
            cell.source += "\n\nstatic-preprocessor-marker"
        return cell, resources


def test_configured_static_preprocessor_is_retained(tmp_path):
    source = _write(tmp_path, [nbformat.v4.new_markdown_cell("original")])

    content, _metadata = IPYNBReader(
        _settings(tmp_path, IPYNB_PREPROCESSORS=(AppendStaticMarker,))
    ).read(str(source))

    assert "static-preprocessor-marker" in content


def test_execution_preprocessor_is_rejected_before_conversion(tmp_path):
    from nbconvert.preprocessors import ExecutePreprocessor

    source = _write(tmp_path, [nbformat.v4.new_code_cell("raise AssertionError")])

    with pytest.raises(NotebookConversionError) as raised:
        IPYNBReader(
            _settings(tmp_path, IPYNB_PREPROCESSORS=(ExecutePreprocessor,))
        ).read(str(source))

    assert raised.value.category == "conversion_failed"
    assert raised.value.cause_type == "ValueError"
    assert "must not contain ExecutePreprocessor" in raised.value.cause_message


def test_original_notebook_copy_uses_safe_deterministic_path(tmp_path):
    source = _write(
        tmp_path,
        [nbformat.v4.new_markdown_cell("copy source")],
        "Title: Synthetic\nDate: 2026-07-21\nSlug: copy-source",
    )

    _content, metadata = IPYNBReader(
        _settings(tmp_path, IPYNB_NB_SAVE_AS="notebooks/{slug}.ipynb")
    ).read(str(source))

    destination = tmp_path / "output" / "notebooks" / "copy-source.ipynb"
    assert destination.read_bytes() == source.read_bytes()
    assert metadata["nb_path"] == "notebooks/copy-source.ipynb"


@pytest.mark.parametrize(
    "save_as",
    ["../outside.ipynb", "/absolute.ipynb"],
)
def test_unsafe_copy_paths_are_typed(tmp_path, save_as):
    source = _write(tmp_path, [nbformat.v4.new_markdown_cell("copy source")])

    with pytest.raises(NotebookCopyError) as raised:
        IPYNBReader(_settings(tmp_path, IPYNB_NB_SAVE_AS=save_as)).read(str(source))

    assert raised.value.stage == "copy"
    assert raised.value.category == "copy_failed"
    assert raised.value.__cause__ is not None


def test_filesystem_copy_failure_preserves_root_cause(tmp_path, monkeypatch):
    source = _write(tmp_path, [nbformat.v4.new_markdown_cell("copy source")])

    def fail_copy(_source, _destination):
        raise PermissionError("synthetic copy denial")

    monkeypatch.setattr(shutil, "copyfile", fail_copy)

    with pytest.raises(NotebookCopyError) as raised:
        IPYNBReader(
            _settings(tmp_path, IPYNB_NB_SAVE_AS="notebooks/source.ipynb")
        ).read(str(source))

    assert raised.value.cause_type == "PermissionError"
    assert raised.value.cause_message == "synthetic copy denial"
    assert isinstance(raised.value.__cause__, PermissionError)


def test_non_metadata_nbdata_content_is_typed(tmp_path):
    source = _write(
        tmp_path,
        [nbformat.v4.new_markdown_cell("body")],
        "Title: Synthetic\nDate: 2026-07-21\nnot metadata",
    )

    with pytest.raises(MetadataParsingError) as raised:
        IPYNBReader(_settings(tmp_path)).read(str(source))

    assert raised.value.stage == "metadata_parsing"
    assert raised.value.category == "malformed_metadata"
    assert raised.value.cause_type == "MalformedMetadata"


def test_malformed_notebook_is_typed(tmp_path):
    source = tmp_path / "broken.ipynb"
    source.write_text("{not json", encoding="utf-8")
    source.with_suffix(".nbdata").write_text(
        "Title: Synthetic\nDate: 2026-07-21", encoding="utf-8"
    )

    with pytest.raises(NotebookParsingError) as raised:
        IPYNBReader(_settings(tmp_path)).read(str(source))

    assert raised.value.stage == "notebook_parsing"
    assert raised.value.category == "malformed_notebook"
    assert raised.value.__cause__ is not None


def test_conversion_failure_is_typed(tmp_path, monkeypatch):
    source = _write(tmp_path, [nbformat.v4.new_markdown_cell("body")])

    def fail_conversion(*_args, **_kwargs):
        raise RuntimeError("synthetic conversion failure")

    monkeypatch.setattr(
        "pelican.plugins.ipynb_reader.reader.convert_notebook_fragment",
        fail_conversion,
    )

    with pytest.raises(NotebookConversionError) as raised:
        IPYNBReader(_settings(tmp_path)).read(str(source))

    assert raised.value.stage == "conversion"
    assert raised.value.cause_type == "RuntimeError"
    assert raised.value.cause_message == "synthetic conversion failure"
    assert isinstance(raised.value.__cause__, RuntimeError)


def test_invalid_summary_bound_is_typed(tmp_path):
    source = _write(tmp_path, [nbformat.v4.new_markdown_cell("body")])

    with pytest.raises(MetadataValidationError) as raised:
        IPYNBReader(_settings(tmp_path, SUMMARY_MAX_LENGTH=0)).read(str(source))

    assert raised.value.category == "invalid_summary_settings"
    assert raised.value.__cause__ is not None
