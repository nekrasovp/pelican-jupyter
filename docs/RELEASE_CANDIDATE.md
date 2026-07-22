# PLUGIN-003 release-candidate evidence

## Status and boundary

This is evidence for a draft release candidate, not a release declaration.
No distribution identity, tag, GitHub release, PyPI upload, site deployment, or
human visual acceptance is created by PLUGIN-003. PLUGIN-004 and PLUGIN-005
remain blocked on their own separately authorized work.

The rollback point is `main` commit
`e687aaf3a0a27708e6de96c8120168def95bfb44`. Before any later release, the
PLUGIN-003 branch can be closed or its commits reverted without changing a
published package or the external site.

## Hosted compatibility policy

`.github/workflows/test.yml` declares six compatibility entries and one
release-candidate job. Every compatibility entry runs the full test suite,
flake8, isort, Black, mypy, the workflow/security scan, the privacy/scope scan,
the owned-reader no-execution scan, and Git diff checks.

| Entry | Python | Runtime input | Purpose |
| --- | --- | --- | --- |
| declared minimum | 3.10 | `requirements-min.txt` | Pelican 4.10.2, nbconvert 7.16.6, nbformat 5.10.4, Jinja2 3.1.4, Markdown 3.6 |
| latest compatible | 3.10 | `requirements.txt` | latest resolution within the declared Pelican 4.x, nbconvert 7.x, nbformat 5.x, Jinja2 3.x, and Markdown 3.x ranges |
| latest compatible | 3.11 | `requirements.txt` | same ranges on Python 3.11 |
| current lock | 3.12 | `requirements-dev.lock.txt` | Pelican 4.12.0, nbconvert 7.17.1, nbformat 5.10.4, Jinja2 3.1.6, Markdown 3.10.2 |
| latest compatible | 3.13 | `requirements.txt` | same ranges on Python 3.13 |
| explicit Pelican | 3.13 | `requirements.txt` plus `ci/constraints-pelican412.txt` | Pelican 4.12.0 explicitly |

All jobs install the exact quality-tool versions in `requirements-ci.txt` or
the exact current lock. Each hosted log prints the exact Python, pip, runtime,
test-tool, and complete resolved package versions; the draft PR records the run
URL. A range is not narrowed without a repeatable hosted failure and a recorded
decision.

The workflow has top-level `contents: read` permission, no secret reference,
no external write action, and full-commit pins for its two allowed actions.
The release-candidate artifacts are retained only inside the hosted job; they
are inspected, not uploaded or published.

## Independent publication gate

`pelican.plugins.ipynb_reader.publication` accepts publisher-owned expected
route/source TSV and metadata JSON files at runtime. It does not contain a
process-global collector and the distribution does not vendor the external
manifest, notebook paths, article text, or site assets.

For every expected notebook the gate independently checks:

- the source and produced route exist;
- actual normalized reader title, date, summary, category, and tags agree with
  rendered article metadata and the applicable baseline fields;
- actual reader metadata records the notebook marker and HTML contract, and an
  authored `lang` value must agree with the publisher target when present;
- publisher-owned target language agrees between the route inventory and
  metadata baseline;
- `cell` and `input_area` class tokens remain present;
- `jp-*` classes and nested fragment documents remain absent; and
- representative committed Markdown, code, PNG, SVG, table, error, image, and
  rich-output modes remain represented where the corpus contains them.

Failure is a typed `NotebookPublicationError` with publication-facing stage,
category, source, and route context. Deleting one expected notebook result
returns exit 1 with category `missing_expected_route`, independently of the
earlier Pelican exit code.

## External compatibility evidence

The public read-only corpus is
`nekrasovp/nekrasovp.github.io@cac7d59b7a691ebdedea17f5978ce24693830bf8`.
The hosted job checks out that exact commit and consumes its canonical
`migration/production_parity/inputs/legacy_routes.tsv` and
`migration/production_parity/baseline/metadata.json` at runtime.

The build configuration is generated outside the external checkout. Its
vendored historical reader is not patched or used as the implementation. The
built PLUGIN-003 wheel is installed into the external locked runtime, then the
corpus is built twice. Both runs must produce deterministic machine-readable
route, normalized-metadata, content-class, source-hash, output-mode, and warning
evidence for exactly 35 Markdown plus 11 notebook articles, 46 total.

The integration instruments both runs and requires zero notebook-client
execution calls, zero kernel starts, zero IPv4/IPv6 connection attempts, no
execution marker, no new execution output, and unchanged `.ipynb`/`.nbdata`
source hashes. A nonexistent kernelspec remains valid because conversion is
static.

## Metadata authority and recorded gaps

The evidence keeps three layers separate instead of treating them as one
matching value:

1. **Publisher target/inventory:** route, date, language, and historical title
   label from the external route TSV, plus page title/language from the
   external metadata baseline.
2. **Actual article metadata:** normalized values read from the adjacent
   `.nbdata`. At the pinned commit, all 11 notebook records have no authored
   `lang`; their actual titles match rendered Open Graph titles and the title
   portion of the baseline page metadata.
3. **Rendered theme observation:** page title and root HTML `lang` parsed from
   generated output. The historical theme renders root `lang="en"` for all 11
   notebooks.

This produces three explicit, narrowly counted deviations at the pinned
commit:

- 8 of 11 historical route-inventory title labels differ from the actual
  `.nbdata` reader title. The affected sources are `mkrf-spb-geo-data.ipynb`,
  `covid-dashboard.ipynb`, `Use Cython to speed up your Python code.ipynb`,
  `Number-sequences.ipynb`, `Stock-market-portfolio-optimisation.ipynb`,
  `stock-perfomance-analysis.ipynb`,
  `Testing-hypothesis-on-football-data-set.ipynb`, and
  `feature-engineering-on-ohlcv-candles-wit-xgboost.ipynb`.
- Actual reader `lang` is absent for all 11 notebook sources. In particular,
  the reader output for `mkrf-spb-geo-data.ipynb` does not contain the
  publisher target `ru`.
- The rendered root language differs from the publisher target for that one
  Russian notebook (`ru` target versus observed `en`).

Owner and follow-up: **SITE-003** owns reconciliation of canonical site
metadata and theme language. PLUGIN-003 records the gaps and fails if their
counts change; it does not edit external content or theme code and does not
claim language acceptance. Machine evidence emits separate `publisher_target`,
`metadata`, `baseline_metadata`, and `rendered_observation` objects for every
notebook.

## Image-alt warning ledger

The narrow ledger records existing external content rather than suppressing
warnings globally. The independent gate observes 57 generated fallback alts in
nine notebook sources and two authored empty `alt` attributes. Pelican's
process-level log contains eight warning records: six distinct nbconvert
records totaling 48 images plus the two empty-alt records. Repeated identical
three-image messages are rate-filtered by the logging path; the per-source gate
is the authoritative count.

| External source | Generated fallback alts | Empty authored alts |
| --- | ---: | ---: |
| `Getting-stock-data-with-pandas-datareader.ipynb` | 3 | 0 |
| `Number-sequences.ipynb` | 23 | 0 |
| `Stock-market-portfolio-optimisation.ipynb` | 5 | 0 |
| `Testing-hypothesis-on-football-data-set.ipynb` | 3 | 0 |
| `Use Cython to speed up your Python code.ipynb` | 0 | 0 |
| `covid-dashboard.ipynb` | 7 | 0 |
| `feature-engineering-on-ohlcv-candles-wit-xgboost.ipynb` | 8 | 0 |
| `markov-chain-bean-machine.ipynb` | 3 | 1 |
| `mkrf-spb-geo-data.ipynb` | 0 | 0 |
| `pascals-triangle.ipynb` | 2 | 1 |
| `stock-perfomance-analysis.ipynb` | 3 | 0 |

Owner: external publisher/content. Rationale: these are pre-existing committed
notebook outputs and source images; editing personal notebook content is
outside PLUGIN-003. Follow-up: a separately scoped site/content accessibility
review may replace fallback or empty alts. The hosted allowlist accepts only
these exact counts at the pinned commit and fails on any other warning.

## Synthetic and artifact evidence

`examples/visual-review/content/contract-v1.ipynb` is a versioned generic
fixture with Markdown, code, PNG, SVG, table, committed error, HTML, and script
outputs plus a nonexistent kernelspec. Its exact `nbconvert-basic.v1` fragment
is a regression fixture. The visual-review README gives an original-zoom human
handoff; independent visual acceptance remains explicitly pending.

The RC job builds one wheel and one sdist. `twine check` and
`ci/verify_artifacts.py` verify metadata, Apache-2.0 license, provenance,
Python policy, SHA-256, and full file lists. The wheel excludes tests,
notebooks, and examples. The sdist contains the generic synthetic notebook,
metadata, visual handoff, exact fragment, contract, license, and provenance.
Separate clean environments install the wheel and sdist, import the reader from
`site-packages`, run `pip check`, and build a one-article example from each
artifact rather than from the checkout.

## Reproduction commands

From a clean plugin checkout with the committed current environment installed:

```sh
python -m pytest
make check
python ci/check_no_execution.py
python ci/check_scope.py
python ci/check_workflow.py
git diff --check
python -m build --no-isolation --wheel --sdist --outdir "$RC_WORK/dist"
python -m twine check "$RC_WORK"/dist/*
python ci/verify_artifacts.py --dist "$RC_WORK/dist" \
  --requirements requirements.txt \
  --work-root "$RC_WORK/installs" \
  --report-out "$RC_WORK/artifacts.json"
```

After installing that wheel into the pinned external runtime:

```sh
"$SITE_ROOT/.venv/bin/python" ci/external_corpus.py \
  --site-root "$SITE_ROOT" \
  --external-commit cac7d59b7a691ebdedea17f5978ce24693830bf8 \
  --expected-manifest \
    "$SITE_ROOT/migration/production_parity/inputs/legacy_routes.tsv" \
  --baseline-metadata \
    "$SITE_ROOT/migration/production_parity/baseline/metadata.json" \
  --work-root "$RC_WORK/external" \
  --report-out "$RC_WORK/external.json" \
  --expected-articles 46 --expected-notebooks 11 \
  --expected-missing-alt 57 --expected-empty-alt 2 \
  --expected-title-gaps 8 --expected-reader-language-absent 11 \
  --expected-rendered-language-gaps 1 --metadata-gap-owner SITE-003 \
  --timezone Europe/Moscow
```

## Known limitations

- Notebook HTML and JavaScript remain trusted authored content; the reader does
  not sanitize them.
- A historical widget output emits a random DOM identifier. Deterministic
  evidence intentionally compares routes, normalized metadata, class tokens,
  source hashes, modes, and warnings rather than claiming byte-identical full
  HTML.
- Canonical/source/theme title and language gaps are recorded above with owner
  SITE-003; they are deviations, not matching-language acceptance.
- Image-alt remediation and human theme review are follow-ups, not silently
  claimed acceptance.
- Artifact filenames and SHA-256 values are commit-derived and are recorded in
  the hosted report and draft PR, not treated as a final distribution identity.
