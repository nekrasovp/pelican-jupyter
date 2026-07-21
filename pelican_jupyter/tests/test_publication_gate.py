from __future__ import annotations

import json
from html import escape

import nbformat
import pytest
from jupyter_client import KernelManager
from nbclient import NotebookClient
from pelican.settings import read_settings

from pelican.plugins.ipynb_reader import IPYNBReader, NotebookPublicationError
from pelican.plugins.ipynb_reader.publication import validate_publication


def _plain(value):
    return str(value).removeprefix("<p>").removesuffix("</p>")


def _fixture(tmp_path, *, html_transform=lambda value: value):
    content = tmp_path / "content"
    output = tmp_path / "output"
    content.mkdir()
    output.mkdir()
    notebook = nbformat.v4.new_notebook(
        metadata={
            "kernelspec": {
                "display_name": "Definitely not installed",
                "language": "python",
                "name": "definitely-not-installed",
            }
        },
        cells=[
            nbformat.v4.new_markdown_cell("Generic publication fixture."),
            nbformat.v4.new_code_cell(
                "raise AssertionError('must not execute')",
                execution_count=7,
                outputs=[
                    nbformat.v4.new_output(
                        "stream", name="stdout", text="COMMITTED_OUTPUT\n"
                    )
                ],
            ),
        ],
    )
    source = content / "synthetic.ipynb"
    nbformat.write(notebook, source)
    source.with_suffix(".nbdata").write_text(
        "\n".join(
            [
                "Title: Synthetic publication",
                "Date: 2026-07-22",
                "Category: Examples",
                "Tags: generic, fixture",
                "Slug: synthetic-publication",
                "Summary: Generic publication summary.",
            ]
        ),
        encoding="utf-8",
    )
    markdown = content / "synthetic-markdown.md"
    markdown.write_text(
        "Title: Synthetic Markdown\nDate: 2026-07-21\n\nBody.\n",
        encoding="utf-8",
    )

    settings = read_settings(
        override={
            "OUTPUT_PATH": str(output),
            "PATH": str(content),
            "TIMEZONE": "UTC",
        }
    )
    fragment, metadata = IPYNBReader(settings).read(str(source))
    summary = _plain(metadata["summary"])
    article = f"""<!doctype html>
<html lang="en"><head>
<title>Synthetic publication - Fixture</title>
<meta name="description" content="{escape(summary)}">
<meta property="og:title" content="Synthetic publication">
<meta property="article:published_time" content="2026-07-22T00:00:00+00:00">
<meta property="article:section" content="Examples">
<meta property="article:tag" content="generic">
<meta property="article:tag" content="fixture">
</head><body><div class="entry-content">{fragment}</div></body></html>
"""
    (output / "synthetic-publication.html").write_text(
        html_transform(article), encoding="utf-8"
    )
    (output / "synthetic-markdown.html").write_text(
        "<!doctype html><html><body>Markdown.</body></html>", encoding="utf-8"
    )

    manifest = tmp_path / "expected.tsv"
    manifest.write_text(
        "route\tpublished_at\tlanguage\tstatus\tsource\ttitle\n"
        "/synthetic-markdown.html\t2026-07-21\ten\tkeep\t"
        "synthetic-markdown.md\tSynthetic Markdown\n"
        "/synthetic-publication.html\t2026-07-22\ten\tkeep\t"
        "synthetic.ipynb\tSynthetic publication\n",
        encoding="utf-8",
    )
    baseline = tmp_path / "metadata.json"
    baseline.write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "description": "Body.",
                        "lang": "en",
                        "path": "/synthetic-markdown.html",
                        "publication_date": "2026-07-21",
                        "source_kind": "markdown",
                        "title": "Synthetic Markdown - Fixture",
                    },
                    {
                        "description": summary,
                        "lang": "en",
                        "path": "/synthetic-publication.html",
                        "publication_date": "2026-07-22",
                        "source_kind": "notebook",
                        "title": "Synthetic publication - Fixture",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    return content, output, manifest, baseline, source


def _validate(content, output, manifest, baseline):
    return validate_publication(
        expected_manifest=manifest,
        baseline_metadata=baseline,
        content_root=content,
        output_root=output,
        external_commit="fixture-commit",
        expected_articles=2,
        expected_notebooks=1,
        expected_missing_alt=0,
        expected_empty_alt=0,
        timezone="UTC",
    )


def test_instance_local_gate_emits_deterministic_route_metadata_and_class_evidence(
    tmp_path,
):
    fixture = _fixture(tmp_path)

    first = _validate(*fixture[:4])
    second = _validate(*fixture[:4])

    assert first == second
    assert first["counts"] == {"articles": 2, "markdown": 1, "notebooks": 1}
    notebook = next(row for row in first["records"] if row["source_kind"] == "notebook")
    assert notebook["metadata"] == {
        "category": "Examples",
        "date": "2026-07-22",
        "language": None,
        "summary": "Generic publication summary.",
        "tags": ["generic", "fixture"],
        "title": "Synthetic publication",
    }
    assert notebook["publisher_target"] == {
        "language": "en",
        "route_inventory_title": "Synthetic publication",
    }
    assert notebook["baseline_metadata"] == {
        "language": "en",
        "page_title": "Synthetic publication - Fixture",
    }
    assert notebook["rendered_observation"] == {
        "html_lang": "en",
        "page_title": "Synthetic publication - Fixture",
    }
    assert notebook["content_modes"] == ["code", "markdown"]


def test_missing_expected_route_is_a_typed_publication_failure(tmp_path):
    content, output, manifest, baseline, _source = _fixture(tmp_path)
    (output / "synthetic-publication.html").unlink()

    with pytest.raises(NotebookPublicationError) as raised:
        _validate(content, output, manifest, baseline)

    assert raised.value.stage.value == "publication_verification"
    assert raised.value.category == "missing_expected_route"
    assert raised.value.cause_type == "MissingExpectedRoute"
    assert raised.value.source_path == "synthetic.ipynb"


def test_missing_expected_source_is_a_typed_publication_failure(tmp_path):
    content, output, manifest, baseline, source = _fixture(tmp_path)
    source.unlink()

    with pytest.raises(NotebookPublicationError) as raised:
        _validate(content, output, manifest, baseline)

    assert raised.value.category == "missing_expected_source"
    assert raised.value.cause_type == "MissingExpectedSource"


@pytest.mark.parametrize(
    ("target_name", "old", "new", "field"),
    [
        (
            "output",
            'property="og:title" content="Synthetic publication"',
            'property="og:title" content="Unexpected title"',
            "og:title",
        ),
        ("baseline", '"lang": "en"', '"lang": "fr"', "language"),
    ],
)
def test_normalized_title_and_canonical_language_drift_are_red(
    tmp_path, target_name, old, new, field
):
    content, output, manifest, baseline, _source = _fixture(tmp_path)
    target = (
        baseline
        if target_name == "baseline"
        else output / ("synthetic-publication.html")
    )
    target.write_text(
        target.read_text(encoding="utf-8").replace(old, new), encoding="utf-8"
    )

    with pytest.raises(NotebookPublicationError) as raised:
        _validate(content, output, manifest, baseline)

    assert raised.value.category == "metadata_mismatch"
    assert raised.value.cause_message.startswith(f"{field}:")


@pytest.mark.parametrize(
    ("transform", "category"),
    [
        (
            lambda html: html.replace('class="cell', 'class = "jp-Cell cell', 1),
            "unsupported_fragment_markup",
        ),
        (
            lambda html: html.replace(
                '<div class="entry-content">',
                '<div class="entry-content"><html><body>',
                1,
            ).replace("</div></body></html>", "</body></html></div></body></html>", 1),
            "nested_fragment_document",
        ),
    ],
)
def test_exact_class_and_nested_document_drift_are_red(tmp_path, transform, category):
    fixture = _fixture(tmp_path, html_transform=transform)

    with pytest.raises(NotebookPublicationError) as raised:
        _validate(*fixture[:4])

    assert raised.value.category == category


def test_gate_normalization_never_starts_a_kernel_or_executes(tmp_path, monkeypatch):
    content, output, manifest, baseline, source = _fixture(tmp_path)
    before = source.read_bytes()
    observations = {"client_executes": 0, "kernel_starts": 0}

    def kernel_started(*_args, **_kwargs):
        observations["kernel_starts"] += 1
        raise AssertionError("publication gate started a kernel")

    def client_executed(*_args, **_kwargs):
        observations["client_executes"] += 1
        raise AssertionError("publication gate executed a notebook")

    monkeypatch.setattr(KernelManager, "start_kernel", kernel_started)
    monkeypatch.setattr(NotebookClient, "execute", client_executed)

    evidence = _validate(content, output, manifest, baseline)

    assert evidence["counts"]["notebooks"] == 1
    assert source.read_bytes() == before
    assert observations == {"client_executes": 0, "kernel_starts": 0}
