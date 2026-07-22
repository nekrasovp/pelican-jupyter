# First-release contract

## Status and interpretation

This document freezes the behavior targeted by the first supported successor
release. It is an implementation and acceptance contract, not evidence that the
legacy code already satisfies it. Support begins only after the required
implementation, compatibility matrix, fixtures, and release validations pass.

The terms **must**, **must not**, **should**, and **may** are normative. When a
legacy behavior conflicts with this document, this document governs the first
release.

## Reader and source model

The release must provide a Pelican Reader for direct `.ipynb` article sources.
For a notebook at `path/article.ipynb`, metadata must come from the adjacent
`path/article.nbdata` file. The `.nbdata` syntax and names are Pelican-compatible
article metadata.

The reader must:

- validate a non-empty `title` and a valid `date` before publishing an article;
- accept an explicit `summary`, or produce a controlled, deterministic summary
  when it is absent;
- support optional `Subcells` selection with documented, validated slice
  semantics;
- optionally copy the original notebook to a configured public destination and
  expose the resulting normalized metadata field;
- convert Markdown, code, image, SVG, table, error, and other rich outputs that
  are already committed in the notebook and supported by the selected
  nbconvert version;
- fail deterministically instead of silently omitting an expected notebook.

Controlled summary generation must be bounded by documented Pelican settings,
must not execute content, and must return stable output for the same notebook,
metadata, configuration, and dependency versions. An explicit summary always
takes precedence.

## Pelican Reader API and metadata

The implementation must use the current Pelican 4 Reader API. Its `read` method
returns `(content, metadata)`. Every metadata value returned to Pelican must be
normalized through the current reader metadata-processing path, including
`BaseReader.process_metadata` or the current documented equivalent, so dates,
authors, categories, tags, and other Pelican-recognized fields have the types
Pelican expects.

Reader-specific metadata, including the notebook-source marker and optional
public notebook path, must be documented and deterministic. Required metadata
validation happens before successful return; raw strings must not bypass the
current Pelican normalization contract.

## Conversion and HTML fragment

Conversion is static. It must not execute cells, start a kernel, invoke an
execution preprocessor, or require a kernel specification to be installed.

The current nbconvert selection for the initial contract is:

```python
HTMLExporter(template_name="basic")
```

The expected result is an embeddable HTML fragment that retains the established
`cell` and `input_area` structure used by the verified integration corpus. The
reader owns conversion and normalized metadata; it must not impose site-wide
theme styles.

Replacing this fragment with a different owned template or materially changing
its markup requires:

1. a new explicit HTML-contract version;
2. updated representative Markdown, code, image, SVG, table, error, and rich
   output fixtures;
3. theme fixture updates; and
4. visual review of the affected states.

Arbitrary historical nbconvert templates are not covered by this contract.

## Deterministic failure contract

Malformed notebooks, missing or malformed `.nbdata`, invalid required metadata,
invalid `Subcells`, conversion failures, and expected notebooks omitted from the
published result must make validation fail.

Reader failures must expose a structured exception with, at minimum:

- `source_path`: the notebook path received by the reader;
- `stage`: metadata discovery, metadata parsing, validation, conversion, copy,
  or publication verification;
- `cause_type`: the root exception type or stable validation category;
- `cause_message`: a concise root-cause description.

The human-readable error must contain the source path, stage, and root cause.
The original exception must be retained with exception chaining where one
exists. Identical invalid input under the same configuration must fail in the
same stage and category. Pelican returning exit code zero is insufficient if an
expected notebook route is absent; publication validation must independently
compare expected and produced notebook sources/routes.

## Security and trust boundary

Notebooks and their committed outputs are authored, trusted publication content.
The reader does not automatically sanitize notebook HTML, JavaScript output, or
external resources. Publishers are responsible for reviewing the content they
commit and the deployment policy that serves it.

The reader must never execute code. Future sanitization modes, interactive
JavaScript policy, or untrusted-notebook handling are separate features requiring
their own contract and review.

PLUGIN-002 and PLUGIN-003 acceptance must include a sentinel notebook containing
code that would create a filesystem marker and attempt a network side effect if
executed. Conversion must render only its committed outputs; no marker, network
request, kernel process, or new executed output may result. The sentinel must run
in both the focused reader suite and the supported build/integration path.

## Initial compatibility target

The evidence matrix initially targets:

- Python 3.10, 3.11, 3.12, and 3.13;
- Pelican 4.x, explicitly including Pelican 4.12;
- current nbconvert 7.x, with one declared minimum and the latest tested 7.x;
- nbformat 5.x and Jinja2 3.x versions selected by the lock/test matrix.

The matrix may narrow a range when repeatable evidence or an upstream dependency
floor requires it. Any narrowing must be documented before release and must not
be presented as broader compatibility. No legacy compatibility claim is valid
without an executable test in the declared matrix.

## Explicitly outside the first release

- Liquid-tag notebook embedding in Markdown;
- Python 2;
- IPython 1.x import or API fallbacks;
- nbconvert 5;
- arbitrary historical or user-supplied templates;
- automatic sanitization of untrusted notebook outputs;
- a general interactive-JavaScript execution policy.

Code for an excluded legacy behavior may remain during staged modernization,
but its presence does not make it supported.

## Distribution identity

The temporary working successor fork is `nekrasovp/pelican-jupyter`.
[ADR 0001](decisions/0001-fork-first-development-identity.md) keeps that
repository and the current package/import compatibility names unchanged for
development and end-to-end plugin/site/theme validation. This does not select
the final distribution identity.

Outreach and the final identity decision resume only after that validation and
a new explicit user decision. Public release remains blocked until the identity
and publication gates are separately satisfied. This contract makes no PyPI
ownership, release-readiness, upstream endorsement, or published-package claim.
