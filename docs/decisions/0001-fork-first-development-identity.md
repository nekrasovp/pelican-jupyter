# ADR 0001: Fork-first development identity

- Status: accepted for development and end-to-end validation
- Date: 2026-07-22
- Owning task: PLUGIN-004, tracked by [issue #4](https://github.com/nekrasovp/pelican-jupyter/issues/4)
- Accepted base: `a292c3951dc4f4ae936a4eeb5d8b05a35643cf50`

## Context

PLUGIN-003 produced accepted release-candidate evidence for the direct reader,
but the plugin, site, and theme have not yet completed their combined
end-to-end validation. The existing public fork at
`nekrasovp/pelican-jupyter` is already the controlled place where the reader
was modernized and tested. Its existence does not establish upstream
endorsement, ownership of the historical `pelican-jupyter` distribution, or
permission to publish under that name.

Contacting maintainers or an organization before the combined integration is
validated would make an external identity decision depend on a candidate that
has not yet been proven through the whole intended route.

## Decision

1. `nekrasovp/pelican-jupyter` is the temporary working successor fork for
   development and end-to-end validation of the plugin/site/theme combination.
2. Maintainer or organization outreach and the final distribution identity are
   deferred until that end-to-end validation is complete. They resume only
   after a new explicit user decision.
3. The repository and package are not renamed now. Distribution metadata,
   import paths, and compatibility behavior remain unchanged; their current
   names are development and compatibility facts, not a publication or
   ownership claim.
4. Public release remains blocked. No tag, GitHub Release, TestPyPI upload,
   PyPI upload, or other package publication is authorized by this decision.
5. Downstream technical integration during validation may use only an
   immutable fork commit or an artifact derived from an identified immutable
   commit. The consumer must verify the commit identifier and, for an
   artifact, a recorded cryptographic digest such as SHA-256. A moving branch,
   an unverified file, or the historical PyPI distribution is not an accepted
   integration source for this work.
6. Issue #4 remains open and deferred. This ADR and its pull request must not
   close it; the issue continues to own the resumed outreach and final identity
   decision.

At the time of this decision, the task has sent zero outreach messages and
created zero package publications.

## Consequences

- Plugin, site, and theme validation can continue against a precise fork
  revision without claiming a final public identity.
- Documentation must describe the fork as a temporary working location and
  keep release instructions blocked.
- The later identity decision requires fresh live evidence and explicit user
  authorization. This ADR does not preselect the canonical, independent, or
  organization-owned distribution path.
- Before publication, this decision can be superseded by a reviewed ADR. Any
  rename or compatibility migration must be separately scoped and tested.
