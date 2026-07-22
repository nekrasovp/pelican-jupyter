# Independent visual-review handoff

This generic synthetic example covers the versioned `nbconvert-basic.v1`
fragment states: Markdown, code, PNG, SVG, table, committed error, and trusted
rich HTML/script output. Its kernelspec intentionally does not exist and its
code cells must never run.

From a clean environment containing an installed candidate artifact and its
runtime dependencies, run:

```sh
python -m pelican content --settings pelicanconf.py --output output \
  --delete-output-directory --fatal errors
```

Open `output/generic-notebook-contract.html` at original browser zoom and review
every state, narrow and wide layouts, source order, readable text, and image
rendering. Confirm that `cell` and `input_area` remain present, no `jp-*` class
or id appears, and no nested fragment document is rendered.

The example deliberately exercises two generated image elements. nbconvert's
generic fallback warning (`Alternative text is missing on 2 image(s).`) is
expected for this synthetic fixture and is not globally suppressed.

Automated fixture and class checks are release-candidate evidence only. Human
visual acceptance remains pending until an independent reviewer records the
candidate commit, artifact filename, browser, viewport, and result.
