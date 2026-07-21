# Legacy-feature inventory

## Purpose

This inventory classifies behavior found in the archived upstream implementation
against the [first-release contract](FIRST_RELEASE_CONTRACT.md). It defines the
modernization boundary; it does not claim that retained targets already work on
the new compatibility matrix.

## Retained contract targets

| Legacy behavior | First-release disposition |
|---|---|
| Direct `.ipynb` Pelican article reader | Retain and modernize against the current Reader API. |
| Adjacent `.nbdata` metadata | Retain; validate required title/date and normalize every returned field. |
| Explicit summary | Retain; it overrides generated summary. |
| Generated summary | Retain with deterministic, documented bounds and fixtures. |
| `Subcells` selection | Retain as optional validated slice behavior. |
| Original-notebook copy (`IPYNB_NB_SAVE_AS`) | Retain as optional behavior with safe paths and normalized result metadata. |
| Committed Markdown/code/image/SVG/table/error/rich outputs | Retain through static nbconvert conversion without execution. |
| Notebook marker and public notebook path metadata | Retain only as documented, deterministic reader-specific fields. |

## Replaced behavior

| Legacy behavior | Replacement |
|---|---|
| `HTMLExporter(template_file="basic")` and nbconvert 5 template lookup | Current `HTMLExporter(template_name="basic")`. |
| Loose metadata return from the Markdown reader | Explicit required-field validation plus current Pelican metadata processing for every field. |
| Unstructured generic exceptions and possible silent omission | Structured deterministic failures with source path, stage, and root cause, plus route/source completeness validation. |
| Implicit compatibility inferred from dependency ranges | An executable Python/Pelican/nbconvert/nbformat/Jinja2 matrix. |
| Theme-specific CSS assumptions inside conversion | A versioned HTML-fragment contract consumed and styled by themes. |
| Historical release commands that assume PyPI access | A release procedure created only after the PLUGIN-004 identity decision and PLUGIN-003 evidence. |

## Deprecated transition candidates

These behaviors are not in the first-release contract. PLUGIN-002 may keep a
bounded compatibility shim only when a migration need and tests justify it:

- metadata extracted from the first notebook cell via
  `IPYNB_MARKUP_USE_FIRST_CELL`;
- the `pelican_jupyter.markup` import path if distribution identity changes;
- legacy `IPYNB_*` setting names whose retained semantics have a tested modern
  implementation;
- CSS filtering and color-scheme options whose output can be expressed without
  violating the owned HTML-fragment boundary.

Deprecated behavior must emit or document a removal path and must not silently
expand the supported first release.

## Removed from first-release support

- Liquid-tag notebook embedding and the vendored Liquid Tags implementation;
- Python 2 branches and `HTMLParser` fallback imports;
- IPython 1.x and other historical IPython import fallbacks;
- nbconvert 5 and its template API;
- arbitrary historical or custom nbconvert templates;
- the historical claim that untested older Pelican or Jupyter combinations are
  likely to work;
- historical release/upload instructions tied to unconfirmed PyPI access.

Removal from support is a contract classification. PLUGIN-001 does not delete
reader code; physical cleanup belongs to a later scoped implementation after
tests preserve the retained behavior.
