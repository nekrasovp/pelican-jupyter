# Release policy

There is no authorized successor release procedure yet.

The archived upstream repository historically published the `pelican-jupyter`
distribution. This fork does not claim PyPI ownership or publishing access, and
its current source is not release-ready. Do not upload this fork to PyPI or Test
PyPI, create a GitHub release, or present an artifact as supported.

Release work is gated as follows:

1. PLUGIN-002 implements the accepted first-release contract.
2. PLUGIN-003 establishes the compatibility matrix, package checks, no-execution
   sentinel, real-corpus evidence, and a reviewed release candidate.
3. PLUGIN-004 records the fork-first development decision in
   [ADR 0001](docs/decisions/0001-fork-first-development-identity.md), using
   `nekrasovp/pelican-jupyter` for end-to-end validation while deferring outreach
   and the final distribution identity until a new explicit user decision.
4. A public-release task remains blocked until the end-to-end path is validated,
   the final identity is explicitly decided, and publication is separately
   authorized.

Downstream validation may pin an immutable fork commit or a commit-derived
artifact with verified integrity. That does not create a supported release.

The [public roadmap](docs/ROADMAP.md) and
[first-release contract](docs/FIRST_RELEASE_CONTRACT.md) are authoritative. A
future release procedure must include wheel and sdist inspection, license and
provenance verification, immutable versioning, and post-publication checks.
