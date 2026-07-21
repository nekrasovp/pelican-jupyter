from __future__ import annotations

from datetime import datetime

import nbformat
import pytest
from pelican.contents import Category, Tag
from pelican.settings import read_settings

from pelican.plugins.ipynb_reader import (
    HTML_CONTRACT_VERSION,
    IPYNBReader,
    MetadataDiscoveryError,
    MetadataValidationError,
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


def _write_notebook(tmp_path, metadata):
    source = tmp_path / "synthetic.ipynb"
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_markdown_cell(
                "# Contract\nDeterministic notebook summary."
            ),
            nbformat.v4.new_code_cell(
                "print('committed')",
                execution_count=7,
                outputs=[
                    nbformat.v4.new_output("stream", name="stdout", text="committed\n")
                ],
            ),
        ]
    )
    nbformat.write(notebook, source)
    source.with_suffix(".nbdata").write_text(metadata, encoding="utf-8")
    return source


def test_reader_returns_normalized_metadata_and_basic_fragment(tmp_path):
    source = _write_notebook(
        tmp_path,
        "\n".join(
            [
                "Title: Synthetic Article",
                "Date: 2026-07-21 10:30",
                "Slug: synthetic-article",
                "Tags: notebooks, testing",
                "Category: Examples",
            ]
        ),
    )

    content, metadata = IPYNBReader(_settings(tmp_path)).read(str(source))

    assert metadata["title"] == "Synthetic Article"
    assert metadata["date"] == datetime(2026, 7, 21, 10, 30)
    assert metadata["slug"] == "synthetic-article"
    assert metadata["tags"] == [
        Tag("notebooks", _settings(tmp_path)),
        Tag("testing", _settings(tmp_path)),
    ]
    assert metadata["category"] == Category("Examples", _settings(tmp_path))
    assert metadata["summary"] == "Contract Deterministic notebook summary."
    assert metadata["jupyter_notebook"] is True
    assert metadata["notebook_html_contract"] == HTML_CONTRACT_VERSION
    assert 'class="cell ' in content
    assert "input_area" in content
    assert "jp-" not in content.lower()
    assert "<html" not in content.lower()
    assert "<body" not in content.lower()


def test_missing_adjacent_metadata_is_typed(tmp_path):
    source = tmp_path / "missing.ipynb"
    nbformat.write(nbformat.v4.new_notebook(), source)

    with pytest.raises(MetadataDiscoveryError) as raised:
        IPYNBReader(_settings(tmp_path)).read(str(source))

    assert raised.value.source_path == str(source)
    assert raised.value.stage == "metadata_discovery"
    assert raised.value.category == "missing_metadata"


@pytest.mark.parametrize(
    ("metadata", "category"),
    [
        ("Date: 2026-07-21", "missing_title"),
        ("Title: Synthetic", "missing_date"),
        ("Title: Synthetic\nDate: not-a-date", "invalid_metadata"),
        ("Title: Synthetic\nDate: 2026-07-21\nSubcells: nope", "invalid_subcells"),
    ],
)
def test_required_metadata_and_subcells_fail_with_stable_categories(
    tmp_path, metadata, category
):
    source = _write_notebook(tmp_path, metadata)

    with pytest.raises(MetadataValidationError) as raised:
        IPYNBReader(_settings(tmp_path)).read(str(source))

    assert raised.value.source_path == str(source)
    assert raised.value.stage == "validation"
    assert raised.value.category == category
