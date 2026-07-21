from __future__ import annotations

import nbformat
import pytest

from pelican.plugins.ipynb_reader import convert_notebook_fragment

PNG_1X1 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "/x8AAusB9Wl2n1cAAAAASUVORK5CYII="
)


@pytest.mark.parametrize(
    ("cell", "expected"),
    [
        (nbformat.v4.new_markdown_cell("**markdown-output**"), "markdown-output"),
        (nbformat.v4.new_code_cell("value = 7"), "input_area"),
        (
            nbformat.v4.new_code_cell(
                "display_png()",
                execution_count=1,
                outputs=[
                    nbformat.v4.new_output(
                        "display_data", data={"image/png": PNG_1X1}, metadata={}
                    )
                ],
            ),
            "data:image/png;base64",
        ),
        (
            nbformat.v4.new_code_cell(
                "display_svg()",
                execution_count=2,
                outputs=[
                    nbformat.v4.new_output(
                        "display_data",
                        data={"image/svg+xml": "<svg><circle r='2'/></svg>"},
                        metadata={},
                    )
                ],
            ),
            "data:image/svg+xml;base64",
        ),
        (
            nbformat.v4.new_code_cell(
                "table",
                execution_count=3,
                outputs=[
                    nbformat.v4.new_output(
                        "execute_result",
                        execution_count=3,
                        data={
                            "text/html": "<table><tr><td>table-cell</td></tr></table>"
                        },
                        metadata={},
                    )
                ],
            ),
            "table-cell",
        ),
        (
            nbformat.v4.new_code_cell(
                "raise ValueError('synthetic')",
                execution_count=4,
                outputs=[
                    nbformat.v4.new_output(
                        "error",
                        ename="ValueError",
                        evalue="synthetic",
                        traceback=["ValueError: synthetic"],
                    )
                ],
            ),
            "ValueError",
        ),
        (
            nbformat.v4.new_code_cell(
                "trusted_rich_output()",
                execution_count=5,
                outputs=[
                    nbformat.v4.new_output(
                        "display_data",
                        data={
                            "text/html": (
                                "<div data-rich='yes'>rich-output</div>"
                                "<script>window.syntheticRich = true;</script>"
                            )
                        },
                        metadata={},
                    )
                ],
            ),
            "window.syntheticRich = true",
        ),
    ],
    ids=["markdown", "code", "png", "svg", "table", "error", "rich-html-script"],
)
def test_committed_output_class_is_preserved(cell, expected):
    notebook = nbformat.v4.new_notebook(cells=[cell])

    fragment = convert_notebook_fragment(notebook)

    assert expected in fragment
    assert "jp-" not in fragment.lower()
    assert "<html" not in fragment.lower()
    assert "<body" not in fragment.lower()


@pytest.mark.parametrize(
    ("fragment", "message", "cell_type"),
    [
        (
            "<html><body><div class='cell'></div></body></html>",
            "wrapper",
            "markdown",
        ),
        ("<div class = 'jp-Cell cell'></div>", "jp-*", "markdown"),
        ("<div>missing contract</div>", "required cell", "markdown"),
        ("<div class='not-cell'></div>", "required cell", "markdown"),
        (
            "<div class='cell'><script>const input_area = true;</script></div>",
            "required input_area",
            "code",
        ),
        (
            "<div class='cell not-input_area'></div>",
            "required input_area",
            "code",
        ),
    ],
)
def test_fragment_boundary_rejects_contract_drift(
    monkeypatch, fragment, message, cell_type
):
    class DriftExporter:
        def __init__(self, *, template_name):
            assert template_name == "basic"

        def from_notebook_node(self, _notebook):
            return fragment, {}

    monkeypatch.setattr(
        "pelican.plugins.ipynb_reader.conversion.HTMLExporter", DriftExporter
    )

    cell = (
        nbformat.v4.new_code_cell("x = 1")
        if cell_type == "code"
        else nbformat.v4.new_markdown_cell("x")
    )
    with pytest.raises(ValueError, match=message):
        convert_notebook_fragment(nbformat.v4.new_notebook(cells=[cell]))
