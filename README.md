# Personal Skills

Reusable agent skills maintained by Jianbo He.

| Skill | Purpose |
| --- | --- |
| [emqx-pr-publication](skills/emqx-pr-publication/SKILL.md) | Prepare and publish EMQX-family pull requests. |
| [emqx-hot-patch-package](skills/emqx-hot-patch-package/SKILL.md) | Package compiled EMQX beam hot patches with a customer README and checksums. |

## Local installation

Clone this repository and link the desired skill directories into your agent's
skill discovery directory. For the shared `~/.agents/skills` layout:

```sh
git clone git@github.com:hjianbo/skills.git
cd skills
mkdir -p "$HOME/.agents/skills"
ln -s "$PWD/skills/emqx-pr-publication" "$HOME/.agents/skills/emqx-pr-publication"
ln -s "$PWD/skills/emqx-hot-patch-package" "$HOME/.agents/skills/emqx-hot-patch-package"
```

If a destination already exists, inspect and back it up before replacing it.
Links expose local changes
immediately; use `git pull --ff-only` in the clone to update from this repository.

The packaging helper requires Python 3. Erlang is optional for extracting beam
MD5 metadata. Run it with `--help` for the supported arguments.

## Maintenance

Edit these first-party skills here and commit verified changes. Keep third-party
skills installed from their own upstream sources; this repository does not vendor
them. Personal AGENTS rules, memories, credentials, and generated patch packages
do not belong in this repository.
