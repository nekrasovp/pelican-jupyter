# Direct notebook reader

## Scope and loading

`pelican.plugins.ipynb_reader` is the single implementation of the direct
`.ipynb` reader. It reads metadata only from the adjacent `.nbdata` file. The
historical `pelican_jupyter.markup` module is a deprecated thin re-export for
the repository's demonstrated legacy import path; it contains no reader or
conversion implementation. First-cell metadata and Liquid-tag embedding are
not supported by this reader.

Pelican can load the namespace plugin explicitly during development:

```python
MARKUP = ("ipynb",)
PLUGINS = ["pelican.plugins.ipynb_reader"]
```

Installed namespace-plugin auto-discovery is also supported when `PLUGINS` is
left at its default of `None`.

## Metadata

The reader requires one non-empty `Title` and one valid `Date`. It normalizes
all `.nbdata` values through Pelican's current Markdown reader and
`BaseReader.process_metadata` path. This gives Pelican-native `datetime`,
`Tag`, `Category`, and `Author` values instead of returning raw metadata
strings.

The stable reader-owned metadata is:

- `jupyter_notebook`: `True`;
- `notebook_html_contract`: `nbconvert-basic.v1`;
- `subcells`: a validated `(start, end)` tuple when selected;
- `nb_path`: a normalized POSIX-relative public path when source copy is
  configured.

An explicit `Summary` is processed as Pelican-formatted metadata and always
wins. Otherwise the reader creates a deterministic plain-text summary from the
converted fragment. `SUMMARY_MAX_LENGTH` is the positive word bound and
`SUMMARY_END_SUFFIX` is appended only when truncation occurs.

## Optional settings

`Subcells` uses a zero-based, half-open `[start:end)` slice. Its syntax is a
two-item tuple or list. `start` must be a non-negative integer; `end` must be
`None` or an integer greater than or equal to `start`.

`IPYNB_PREPROCESSORS` accepts an iterable of static nbconvert preprocessors.
The reader rejects nbconvert's `ExecutePreprocessor` class and subclasses
before conversion. Publisher-configured preprocessors remain trusted build
code and should be reviewed like Pelican configuration.

`IPYNB_NB_SAVE_AS` optionally copies the original notebook beneath
`OUTPUT_PATH`. It is formatted with normalized metadata, must remain a safe
relative POSIX path, and cannot contain `..` or escape the output root.

## HTML contract and trust boundary

Contract `nbconvert-basic.v1` is isolated in one conversion function and uses
exactly:

```python
HTMLExporter(template_name="basic")
```

The result is a fragment with the `cell` and, for code cells, `input_area`
structure. Conversion fails if a nested `html`/`body` wrapper or `jp-*` markup
appears. The reader preserves supported committed Markdown, code, PNG, SVG,
table, error, HTML, and script outputs. Those outputs are trusted authored
publication content; the reader does not claim to sanitize them.

The reader does not execute cells, call a notebook client, start a kernel, or
require the notebook's kernelspec to exist. The focused and Pelican-build
sentinels contain code that would create a marker and make a network request;
tests observe that neither side effect occurs and that committed output and
source bytes remain unchanged.

## Structured failures and publication verification

All `read()` failures derive from `NotebookReaderError` and expose
`source_path`, `stage`, `category`, `cause_type`, and `cause_message`. Concrete
types cover metadata discovery, metadata parsing, validation, notebook parsing,
conversion, and copy. When an underlying exception exists it is retained via
exception chaining.

`NotebookPublicationError` provides the same structure for
publication-facing omissions. The instance-local
`pelican.plugins.ipynb_reader.publication` CLI independently compares a
publisher-owned expected source/route manifest and metadata baseline with one
completed output tree. It returns non-zero for a missing source or route even
when Pelican returned zero. The plugin does not retain process-global build
state and does not vendor a publisher's manifest.

## Dependency policy

The runtime policy is Python `>=3.10,<3.14`, Pelican `>=4.10.2,<5`, nbconvert
`>=7.16.6,<8`, nbformat `>=5.10.4,<6`, Markdown `>=3.6,<4`, and Jinja2
`>=3.1.4,<4`. `requirements-min.txt` records the exact direct floors used for
the local minimum smoke. `requirements-dev.lock.txt` records the resolved
current development environment and is installed with
`uv pip install -r requirements-dev.lock.txt`. The hosted matrix and
release-candidate evidence are recorded in
[the PLUGIN-003 report](RELEASE_CANDIDATE.md). It may narrow these provisional
ranges only when repeatable evidence and the decision are documented.
