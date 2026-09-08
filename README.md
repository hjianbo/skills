# Personal Codex Setup

Rebuild Jianbo He's global instructions, skills, and enabled plugins on a fresh
Linux or macOS Codex CLI environment.

## Install

Prerequisites: Python 3.10+, Git, Node.js/npm (`npx`), and a logged-in Codex CLI
with `codex plugin add` and `codex plugin list --json` support.
This repository is private; the clone step also needs GitHub access.

With GitHub CLI already authenticated:

```sh
gh repo clone hjianbo/skills && python3 skills/bootstrap.py --apply
```

Or clone over SSH and run:

```sh
git clone git@github.com:hjianbo/skills.git
python3 skills/bootstrap.py --apply
```

Keep the checkout: installed instructions and first-party skills link to it.
Without `--apply`, the script only prints its plan and does not run installers.

## Managed content

| Source | Installed content |
| --- | --- |
| [global/AGENTS.md](global/AGENTS.md) | Global personal instructions |
| This repository | `emqx-pr-publication`, `emqx-hot-patch-package` |
| `mattpocock/skills` | `grilling` only |
| `vercel-labs/skills` | `find-skills` only |
| `mvanhorn/last30days-skill` | `last30days` only |
| Codex remote marketplace | Superpowers, Deep Research, Plugin Management, OpenAI Templates |

[bootstrap.json](bootstrap.json) is the installation manifest. Third-party sources
remain upstream-managed; the Skills CLI version is pinned. A fresh installation
gets the versions available from those sources at installation time, not a
byte-identical snapshot of this computer. Actual plugin versions and skill source
hashes are recorded locally in `~/.agents/bootstrap-result.json`.

The bootstrap does not migrate credentials, auth sessions, memories, project
AGENTS, model/provider choices, MCP connections, permissions, or caches.
Disabled Ponytail is not installed. Account-provided system skills remain managed
by Codex. Remote plugins depend on availability to the destination account;
unavailable plugins cause a clear failure rather than a false success.
Research services may need their own credentials after installation.

## Update and recovery

```sh
git pull --ff-only
python3 bootstrap.py --apply
```

A normal rerun skips installed upstream skills with the expected source and
enabled plugins. To refresh those managed dependencies too:

```sh
python3 bootstrap.py --apply --update
```

Before replacing files, the script backs them up under
`~/.agents/backups/bootstrap-*/`. Each numbered backup folder contains an
`original-path.txt` and the original file or directory. Existing Codex config and
the Skills CLI lock are also backed up before invoking installers. Unrelated
skills and settings are retained.

If an installation fails, completed steps remain in place; correct the reported
problem and rerun. Backups are not automatically deleted. To restore an older
file, inspect its recorded destination, move the replacement aside, and restore
the backup there. This is file recovery, not automatic rollback of remote plugin
installations.

`CODEX_HOME`, when set, selects the Codex configuration directory; shared skills
remain in `~/.agents/skills`. Start a new Codex session after installation.

## Maintenance

Edit global instructions in `global/AGENTS.md`, personal skills in `skills/`,
and sources in `bootstrap.json`. Do not commit secrets or generated packages.
Shared policy belongs in AGENTS; skills contain only task-specific guidance.

```sh
python3 -m unittest discover -s tests
python3 bootstrap.py
```

The bootstrap tests use temporary homes and simulated installer commands; they
do not install plugins into your account. The packaging helper tests cover zip
contents and overwrite protection, not runtime EMQX hot loading.
