# Personal Agent Guidance

Source: `hjianbo/skills/global/AGENTS.md`, installed as `~/.agents/AGENTS.md`
and linked into Codex. Grok and OpenCode may share the same file via symlinks.
Repository-specific rules live in each repo's `AGENTS.md`.

## Working Agreements

- Communicate in concise Chinese; use concise English for GitHub and customer-facing text unless requested otherwise.
- Read the actual checkout and relevant logs before concluding. Preserve unrelated local changes.
- Review and diagnosis requests deliver evidence and conclusions; implement only when requested.
- Complete the endpoint authorized by this request and earlier decisions. Do not ask again about established choices or present delivery options after I have chosen the endpoint.
- For small changes with clear requirements and acceptance criteria, proceed directly to implementation and verification. Skip brainstorming approval gates, separate design documents, and plan documents for these tasks.
- Use design interviews for consequential unresolved choices. Ask only when missing information materially changes the result and cannot be inferred from available evidence; continue independent work while waiting.
- Reply to or resolve GitHub review threads only when explicitly requested.
- Cleanup only named artifacts after verifying live merge state, target ancestry, and local changes.

## Evidence and Verification

- Verify exact checkout and code path; for PR work, refresh live head/base, unresolved threads, and relevant CI.
- Distinguish protocol intent from repository behavior, and confirmed facts from hypotheses.
- Prefer reproduction when feasible. Without it, continue source/log analysis and state missing runtime validation; diagnosis need not include a fix.
- Run relevant checks and report results, unavailable checks, and unrelated baseline failures explicitly.
- Report code-review findings as numbered items with priority, blocker status, and file/line evidence; explicitly state when none remain.

## Skills and Memory

- Default to Superpowers for engineering work when available, within the scope and lightweight-task exceptions above. Skill instructions do not add authorization.
- Use Matt's `grilling` only when explicitly asked to probe or challenge a plan. Do not repeat it and `brainstorming` for an already-settled design.
- Use `last30days` for explicit recent community/sentiment research or when named; use `find-skills` for explicit skill discovery/installation. Ordinary questions do not trigger these workflows.
- Keep third-party skills on their upstream update path; personal overrides belong here. User requirements take precedence over skill output templates.
- Shared skills: `~/.agents/skills/`. Shared memory: `~/.agents/memory/MEMORY.md`.
- For non-trivial work, consult relevant memory routing when present. A fresh environment may have no memories. Treat historical branches, versions, and implementation notes as leads to verify, not current facts.
- Keep policies here or in repository AGENTS; memory holds stable background and retrieval hints. On an explicit remember request, record a short durable note through the environment's supported memory-update mechanism.
- Deep history: `~/.codex/memories/` and `~/.grok/memory/`; retrieve only task-relevant records.

## EMQX-Family Repositories

Applies to EMQX repositories, docs, and related plugins, including `emqx_whc` and `emqx_sync_request`.

- Use `emqx-pr-publication` for PR preparation/publication and `emqx-hot-patch-package` for customer beam packages.
- Keep branch names and PR titles free of tooling markers such as `codex`, `grok`, and `opencode`.
- Follow the PR template; omit standalone validation sections and local command logs unless required. Report local commands/results to me.
- Fill required ticket and fix/release version fields from verified context; ask if uncertain.
- Treat feasible `make static_checks` as a code-publication gate. Identify unrelated baseline failures without widening the patch.
- Inspect unresolved threads and exact diff context before responding to review feedback.
- Follow existing repo-local worktree conventions: usually `emqx6/.worktree/<branch>` and classic `emqx/.worktrees/<branch>`.
- Before backporting, check the destination line's existing changes; name changelogs for the destination PR.
