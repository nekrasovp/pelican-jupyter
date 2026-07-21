# Public roadmap

The successor work is deliberately sequential. A later task waits until its
dependency is accepted and merged. Issue links will be added to this document as
the PLUGIN-001 backlog is created.

## PLUGIN-001 — successor fork and contract

Status: in progress in the initial draft pull request.

Creates the public fork with preserved history and license, freezes the
first-release contract and legacy inventory, records governance and repository
state, and creates PLUGIN-002 through PLUGIN-005 issues. It does not modernize
the reader, publish a package, contact upstream, change a site, or merge itself.

## PLUGIN-002 — modernize the reader

Depends on: accepted and merged PLUGIN-001.

Modernize only the direct `.ipynb` plus adjacent `.nbdata` reader to the
[first-release contract](FIRST_RELEASE_CONTRACT.md), including current Pelican
metadata normalization, nbconvert selection, structured failure, and focused
no-execution coverage. Do not publish a package.

Issue: pending creation in PLUGIN-001.

## PLUGIN-003 — CI, compatibility, and release-candidate evidence

Depends on: accepted and merged PLUGIN-002.

Establish the supported dependency matrix, package build checks, synthetic
fixtures, no-execution sentinel, and representative integration evidence. A
missing expected notebook must make validation fail even if Pelican exits zero.
Do not decide or publish the final distribution identity.

Issue: pending creation in PLUGIN-001.

## PLUGIN-004 — bounded outreach and identity decision

Depends on: accepted PLUGIN-003 release-candidate evidence.

After separate authorization, send at most one bounded outreach message and
observe a 10-14 calendar-day response window without repeated polling. Re-check
GitHub and PyPI name availability, then record one identity decision: canonical
`pelican-jupyter` only with explicit access, preferred independent
`pelican-ipynb-reader`, or `pelican-plugins` only on explicit acceptance.

No outreach is sent by PLUGIN-001.

Issue: pending creation in PLUGIN-001.

## PLUGIN-005 — first supported release

Depends on: completed PLUGIN-004 identity decision.

Finalize release documentation, build and inspect distributions, publish through
the approved identity and trusted mechanism, and verify the immutable public
release. PLUGIN-005 must not start while distribution identity is unresolved.

Issue: pending creation in PLUGIN-001.
