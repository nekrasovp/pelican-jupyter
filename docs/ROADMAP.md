# Public roadmap

The successor work is deliberately sequential. A later task waits until its
dependency is accepted and merged.

## PLUGIN-001 — successor fork and contract

Status: in progress in [draft PR #1](https://github.com/nekrasovp/pelican-jupyter/pull/1).

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

Issue: [#2](https://github.com/nekrasovp/pelican-jupyter/issues/2).

## PLUGIN-003 — CI, compatibility, and release-candidate evidence

Depends on: accepted and merged PLUGIN-002.

Establish the supported dependency matrix, package build checks, synthetic
fixtures, no-execution sentinel, and representative integration evidence. A
missing expected notebook must make validation fail even if Pelican exits zero.
Do not decide or publish the final distribution identity.

Issue: [#3](https://github.com/nekrasovp/pelican-jupyter/issues/3).

## PLUGIN-004 — fork-first development decision

Depends on: accepted PLUGIN-003 release-candidate evidence.

Use `nekrasovp/pelican-jupyter` as the temporary working successor fork for
development and end-to-end plugin/site/theme validation. Outreach and the final
distribution identity are deferred until that validation is complete and a new
explicit user decision resumes the work. Do not rename the repository/package,
change imports or compatibility, or create a public release in this task.

Downstream validation may use only an immutable fork commit or a
commit-derived artifact with verified integrity. The
[fork-first decision](decisions/0001-fork-first-development-identity.md) records
the boundary. Issue #4 remains open and deferred; this decision does not close
it. Outbound count and package-publication count remain zero.

Issue: [#4](https://github.com/nekrasovp/pelican-jupyter/issues/4).

## PLUGIN-005 — first supported release

Depends on: resumed and completed final distribution-identity decision after
end-to-end validation.

Finalize release documentation, build and inspect distributions, publish through
the approved identity and trusted mechanism, and verify the immutable public
release. PLUGIN-005 must not start while distribution identity is unresolved.

Issue: [#5](https://github.com/nekrasovp/pelican-jupyter/issues/5).
