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
3. PLUGIN-004 performs at most one authorized outreach message, observes the
   10-14 calendar-day response window, re-checks name availability, and records
   the distribution-identity decision.
4. PLUGIN-005 documents and publishes only under that decided identity.

The [public roadmap](docs/ROADMAP.md) and
[first-release contract](docs/FIRST_RELEASE_CONTRACT.md) are authoritative. A
future release procedure must include wheel and sdist inspection, license and
provenance verification, immutable versioning, and post-publication checks.
