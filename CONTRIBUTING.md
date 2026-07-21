# Contributing

Thank you for helping with the successor fork. Contributions are accepted under
the Apache License 2.0 as described in [LICENSE.txt](LICENSE.txt), including the
license's contribution terms.

## Current boundary

The repository is in a contract-first phase. Before proposing implementation:

1. read the [first-release contract](docs/FIRST_RELEASE_CONTRACT.md);
2. find the owning task in the [public roadmap](docs/ROADMAP.md);
3. discuss scope in that task's GitHub issue;
4. keep one pull request within one task boundary.

Documentation corrections, deterministic test fixtures, compatibility evidence,
and security reports are welcome. A contribution does not grant repository
administration, release authority, PyPI ownership, upstream endorsement, or a
maintainer role. See [GOVERNANCE.md](GOVERNANCE.md).

PLUGIN-001 changes only the public contract and governance baseline. Reader
modernization belongs to PLUGIN-002; CI and release-candidate evidence belong to
PLUGIN-003; identity and any outreach belong to PLUGIN-004; publication belongs
to PLUGIN-005.

## Pull requests

- Base work on the repository's default branch.
- Link the owning issue and state dependencies.
- Include acceptance criteria, exact validation, and rollback notes.
- Preserve upstream history, attribution, and `LICENSE.txt`.
- Do not include private data, personal-site content, secrets, notebook
  execution, or claims unsupported by tests.
- Do not bundle unrelated cleanup or later-roadmap implementation.

Compatibility is established by the supported matrix and fixtures, not by an
untested assertion that a historical option still works.
