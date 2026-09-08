---
name: emqx-pr-publication
description: Use when preparing or publishing EMQX-family pull requests, including branch targeting, release/dev sync, branch naming, PR body fields, validation gates, draft PR creation, and final body review.
---

# EMQX PR Publication

Use this skill for `emqx`, `emqx6`, `emqx-enterprise`, and `emqx-docs` PR publication work.

## Preconditions

1. Verify the repository, current branch, base branch, and dirty worktree.
2. Inspect the repo PR template before drafting the body.
3. Confirm the ticket / issue link and release or fix version. If either is uncertain, ask instead of guessing.
4. Keep branch names and PR titles free of `codex`.

## Branch Targeting and Sync

- Treat memory and local AGENTS as routing hints. Before choosing a base, verify live refs, the issue/Jira target version, the PR template, and whether the upstream commits are already present on the target line.
- For `emqx` release-line sync, create the working branch from the destination remote ref such as `ce/release-*`, merge the source `ce/release-*`, and publish the PR to the destination branch without the `ce/` prefix. Preserve destination-line release metadata while integrating the source-line change.
- For `emqx` dev-line sync or follow-up work, create the working branch from the destination `ce/dev-*`, merge or port the source change into that branch, and publish the PR to the destination `dev-*` branch.
- For `emqx` branch-specific bug fixes and backports, use the user request, Jira/Fix version, issue "Plan to" text, or release-owner instruction as the target hint, then confirm the actual branch/ref before editing. Use `git cherry -v`, `git log --cherry-pick`, or an equivalent check before re-porting commits.
- For `emqx-enterprise`, verify the active enterprise maintenance branch, often shaped like `main-v*-enterprise`, and the branch-local dependency or feature usage path before editing. Do not broaden dependency/security changes to other enterprise lines without confirmation.
- For sync PRs, explain conflict-resolution rationale and confidence in the final report. If the branch policy changes after publication and the commit can stay the same, retarget the live PR instead of recreating it.

## Validation Gate

- Run focused tests that match the touched files.
- Run formatting checks and `git diff --check`.
- For EMQX code changes, treat `make static_checks` as a publish gate when feasible.
- If `make static_checks` fails only on unrelated baseline warnings, identify the untouched baseline files and keep the PR-local claim scoped.
- Do not widen a patch to fix unrelated baseline failures unless explicitly asked.

## PR Body Rules

- Use concise English.
- Fill `Fix version`, `Release version`, `Fix:`, `Fixes`, or ticket fields explicitly when the template asks for them.
- Prefer concrete observed behavior over generic risk language.
- Do not add standalone `Validation`, `Validation performed locally`, or local command-list sections unless the template or user explicitly requires them.
- For sync PRs without a real ticket, use clear `N/A` wording rather than inventing a ticket.

## Publication Steps

1. Review the staged or committed diff locally.
2. Run required focused validation.
3. Push the branch.
4. Create a draft PR unless the user asks for ready-for-review.
5. Re-read the published PR body with `gh pr view --json body,url`.
6. If the body contains unwanted validation logs or guessed fields, edit it immediately.

## Final Report

Report:

- PR URL.
- Base/head branches.
- Validation actually run.
- Any baseline blocker or skipped check.
- Any field that was set to `N/A` and why.
