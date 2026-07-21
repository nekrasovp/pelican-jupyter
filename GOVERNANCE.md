# Governance

## Project boundary

This repository owns the generic Jupyter notebook-to-Pelican reader, its
metadata and HTML-fragment contracts, fixtures, packaging, and releases. It does
not own a theme, a personal site, publication content, biographies, domains,
navigation, feeds, redirects, or deployment settings.

The repository must not depend on a person's name, domain, biography, employer,
social accounts, article slugs, or private content. External sites may be used as
integration corpora without copying their content into this repository unless a
separate explicit license permits that copy.

## Decision and administration boundary

The repository currently lives under the `nekrasovp` GitHub account. Account
owners and explicitly granted repository administrators control visibility,
settings, permissions, branch rules, security settings, and releases. This
document does not enumerate collaborators or expose private permission data.

Issue participation, a pull request, review, or merged contribution does not by
itself grant administration, maintainership, release authority, PyPI ownership,
or authority to speak for the archived upstream or Pelican project. Changes to
maintainer and release roles must be explicit and public.

## Change process

- Public work is tracked in the [roadmap](docs/ROADMAP.md) and owning issue.
- Dependencies must be complete before a later task starts.
- A pull request must state scope, acceptance evidence, validation, and rollback.
- Contract, compatibility, security/trust, HTML-fragment, identity, and release
  changes require explicit review.
- Support claims require executable evidence in the declared matrix.
- Releases require the identity decision and release gates owned by PLUGIN-004
  and PLUGIN-005.

## Security reports

Do not include secrets, private notebooks, or exploit data that would create
avoidable harm in a public issue. Use GitHub's private vulnerability-reporting
channel if it is enabled; otherwise ask in a minimal public issue how to report
privately without disclosing the vulnerability.

Notebook conversion is non-executing, but committed HTML, JavaScript, and
external resources are trusted authored content rather than automatically
sanitized input. Security changes must preserve the boundary in the
[first-release contract](docs/FIRST_RELEASE_CONTRACT.md).
