---
name: emqx-pr-publication
description: Use when preparing or publishing EMQX-family PRs, including backports and branch syncs.
---

# EMQX PR Publication

Apply the user's AGENTS publication rules and authorized endpoint.

1. Verify the destination remote/ref and template. Refresh an existing PR's head,
   base, CI, and unresolved threads.
2. For new work, branch from the destination. For syncs, preserve destination
   release metadata; for backports, check existing changes and use the destination
   PR number for changelogs.
3. Review the scoped diff and complete required checks, including formatting and
   `git diff --check`. Resolve change-related failures before publishing.
4. Describe the problem and resulting behavior. Populate required ticket/version
   fields from evidence; ask only for unresolved values. `N/A` means inapplicable,
   not unknown.
5. When authorized, commit and push; update the existing PR or create a draft
   unless ready-for-review was requested.
6. Verify the live title, body, head/base, and draft state. Report the URL,
   validation limitations, and reasons for `N/A` fields or sync conflict decisions.
