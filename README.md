# pelican-jupyter successor fork

This repository is a public successor-maintenance fork of
[`danielfrg/pelican-jupyter`](https://github.com/danielfrg/pelican-jupyter).
The upstream repository is archived. This fork is independently maintained and
is not endorsed by the upstream author or the Pelican project.

## Project status

The fork is in its contract-first phase. It has **not** published a successor
release and is **not release-ready**. The `pelican-jupyter` name on PyPI remains
an existing historical distribution; this repository does not claim ownership
of it or access to publish it.

The provisional GitHub repository identity is
[`nekrasovp/pelican-jupyter`](https://github.com/nekrasovp/pelican-jupyter).
The distribution identity will be decided only after the bounded identity work
described in the [public roadmap](docs/ROADMAP.md).

Current public project documents:

- [provenance and license](docs/PROVENANCE.md);
- [first-release contract](docs/FIRST_RELEASE_CONTRACT.md);
- [legacy-feature inventory](docs/LEGACY_FEATURE_INVENTORY.md);
- [governance](GOVERNANCE.md) and [contribution boundary](CONTRIBUTING.md);
- [repository settings snapshot](docs/REPOSITORY_SNAPSHOT.md);
- [public roadmap](docs/ROADMAP.md).

The direct reader is being modernized under PLUGIN-002. This repository still
has no supported successor release: the complete compatibility matrix belongs
to PLUGIN-003 and publication remains blocked on the later identity decision.

## First-release direction

The planned first release is a static Pelican reader for direct `.ipynb`
article sources with adjacent `.nbdata` metadata. It converts outputs already
committed in notebooks and never executes cells or starts a kernel. The
[first-release contract](docs/FIRST_RELEASE_CONTRACT.md) is the authoritative,
self-contained scope for implementation and acceptance.

Liquid-tag embedding, Python 2, IPython 1.x fallbacks, nbconvert 5, and
arbitrary historical templates are outside that release. They must not be
treated as supported merely because their legacy code remains in this fork.

## Direct-reader development interface

The implementation lives at `pelican.plugins.ipynb_reader` and registers an
`IPYNBReader` through Pelican's `readers_init` signal. During development it can
be loaded explicitly:

```python
MARKUP = ("ipynb",)
PLUGINS = ["pelican.plugins.ipynb_reader"]
```

For `content/example.ipynb`, create adjacent `content/example.nbdata` metadata:

```text
Title: Synthetic Notebook
Date: 2026-07-21
Slug: synthetic-notebook
Tags: notebooks, synthetic
Category: Examples
```

This is development documentation, not an installation or release claim. The
reader settings, stable metadata, failure model, and no-execution boundary are
documented in [the direct-reader contract](docs/DIRECT_READER.md).

## Historical upstream usage

The archived project exposed two modes:

1. a direct `.ipynb` Pelican reader with adjacent `.nbdata` or metadata in the
   first notebook cell; and
2. Liquid-tag embedding of notebooks inside Markdown content.

The original configuration included settings such as `Subcells`,
`IPYNB_NB_SAVE_AS`, `IPYNB_GENERATE_SUMMARY`, `IPYNB_PREPROCESSORS`, and custom
nbconvert templates. These names are recorded for migration analysis in the
[legacy-feature inventory](docs/LEGACY_FEATURE_INVENTORY.md); they are not a
successor compatibility promise.

For historical source and instructions, consult the
[archived upstream repository](https://github.com/danielfrg/pelican-jupyter).
Installing `pelican-jupyter` from PyPI currently installs the historical
distribution, not a release produced by this successor fork.

## License

The upstream history and attribution are preserved. The repository remains
licensed under the Apache License 2.0; see [LICENSE.txt](LICENSE.txt) and the
[provenance note](docs/PROVENANCE.md).
