---
name: emqx-pr-publication
description: Prepare or publish EMQX-family pull requests, including fixes, backports, and release-line syncs.
---

# EMQX PR Publication

Applies to EMQX repositories, documentation, and related plugins. Follow applicable
AGENTS rules and the user's authorized endpoint; drafting a PR body alone does not
authorize pushing code or creating a PR.

## Target and scope

- Inspect the checkout, dirty files, remotes, destination ref, and PR template.
  Verify branch/version hints from memory against live refs and the issue or release request.
- Start new work from the destination remote ref. For syncs, merge the source line
  into it and preserve destination release metadata. For backports, check what the
  destination already contains before replaying changes; name changelogs for the destination PR.
- Use the actual remote and maintenance branch, not a hard-coded remote name.
  Check enterprise dependencies and feature usage on that branch.
- For an existing PR, refresh its head/base, CI, and unresolved review threads.
  Keep unrelated local changes and review-thread replies outside the publication task.

## Verification

- Review the final diff; run relevant tests, formatting, and `git diff --check`.
- Run `make static_checks` for EMQX code changes when available and feasible.
  Report unavailable checks and identify untouched baseline failures; do not broaden the patch.
  Resolve failures caused by the change before publication.

## Body and publication

- Use concise English describing the problem and resulting behavior. Follow the
  template; omit standalone validation sections and local command logs unless required.
- Fill ticket and fix/release version fields from verified context. Ask if required
  information remains uncertain; do not ask again for an established choice.
  Use `N/A` only when a field is known not to apply, such as a ticketless sync.
- Keep branch names and titles free of tooling markers (`codex`, `grok`, `opencode`).
- When publication is authorized, commit the scoped changes, push, and create a
  draft PR unless ready-for-review was requested. Update an existing PR when appropriate.
- Re-read the live title, body, base/head, and draft state; correct discrepancies.
  Report the URL, base/head, verification results and limitations, and reasons for
  any `N/A` fields or sync conflict decisions.
