#!/usr/bin/env python3
"""Restore personal Codex instructions, skills, and plugins. Preview by default."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def run(command):
    print("$ " + shlex.join(command), flush=True)
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {shlex.join(command)}\n"
            + result.stderr.strip()
        )
    return result.stdout


def validate(root, manifest):
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported bootstrap manifest version")
    if not re.fullmatch(r"\d+\.\d+\.\d+", manifest["skills_cli_version"]):
        raise ValueError("Invalid skills CLI version")
    names = list(manifest["local_skills"]) + [s["name"] for s in manifest["upstream_skills"]]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate skill names")
    for name in names:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
            raise ValueError(f"Invalid skill name: {name}")
    for skill in manifest["upstream_skills"]:
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", skill["source"]):
            raise ValueError("Expected owner/repository for upstream skill source")
    for plugin in manifest["plugins"]:
        if not re.fullmatch(r"[\w.-]+@[\w-]+", plugin):
            raise ValueError(f"Invalid plugin selector: {plugin}")
    required = [root / "global/AGENTS.md"] + [
        root / "skills" / name / "SKILL.md" for name in manifest["local_skills"]
    ]
    for path in required:
        if not path.is_file():
            raise ValueError(f"Missing repository file: {path}")


class Bootstrap:
    def __init__(self, root, home, codex_home, manifest, runner=run):
        self.root = root
        self.home = home
        self.codex_home = codex_home
        self.manifest = manifest
        self.run = runner
        self.agents = home / ".agents"
        self.skills = self.agents / "skills"
        self.backup = None
        self.backed_up = set()

    def backup_path(self, path, move=False):
        if path in self.backed_up or not (path.exists() or path.is_symlink()):
            return
        if self.backup is None:
            parent = self.agents / "backups"
            parent.mkdir(parents=True, exist_ok=True)
            self.backup = Path(tempfile.mkdtemp(prefix="bootstrap-", dir=parent))
            print(f"Backups: {self.backup}")
        slot = self.backup / str(len(self.backed_up))
        slot.mkdir()
        (slot / "original-path.txt").write_text(str(path) + "\n", encoding="utf-8")
        destination = slot / path.name
        if move:
            shutil.move(str(path), str(destination))
        elif path.is_symlink() and not path.is_file():
            destination.symlink_to(os.readlink(path))
        elif path.is_dir():
            shutil.copytree(path, destination, symlinks=True)
        else:
            shutil.copy2(path, destination)
        self.backed_up.add(path)

    def link(self, source, destination):
        if destination.is_symlink() and destination.resolve() == source.resolve():
            return
        self.backup_path(destination, move=True)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(source, target_is_directory=source.is_dir())

    def skill_command(self, skill):
        return ["npx", "--yes", "skills@" + self.manifest["skills_cli_version"],
                "add", skill["source"], "-g", "--skill", skill["name"],
                "--agent", "codex", "--yes"]

    def plugins(self):
        result = json.loads(self.run(["codex", "plugin", "list", "--json"]))
        return {p["pluginId"]: p for p in result["installed"]}

    def preview(self):
        print(f"Link {self.root / 'global/AGENTS.md'} -> {self.agents / 'AGENTS.md'}")
        print(f"Link {self.agents / 'AGENTS.md'} -> {self.codex_home / 'AGENTS.md'}")
        for name in self.manifest["local_skills"]:
            print(f"Link {self.root / 'skills' / name} -> {self.skills / name}")
        for skill in self.manifest["upstream_skills"]:
            print(shlex.join(self.skill_command(skill)))
        for plugin in self.manifest["plugins"]:
            print(shlex.join(["codex", "plugin", "add", plugin]))
        print("Preview only. Pass --apply to install; --update also refreshes managed upstream content.")

    def apply(self, update=False):
        # Query capability/authentication before changing local instructions.
        installed = self.plugins()
        self.backup_path(self.codex_home / "config.toml")
        lock = self.agents / ".skill-lock.json"
        self.backup_path(lock)
        self.backup_path(self.agents / "bootstrap-result.json", move=True)
        self.link(self.root / "global/AGENTS.md", self.agents / "AGENTS.md")
        self.link(self.agents / "AGENTS.md", self.codex_home / "AGENTS.md")
        for name in self.manifest["local_skills"]:
            self.link(self.root / "skills" / name, self.skills / name)
        for skill in self.manifest["upstream_skills"]:
            entries = read_json(lock).get("skills", {}) if lock.exists() else {}
            entry = entries.get(skill["name"], {})
            target = self.skills / skill["name"]
            if (not update and entry.get("source") == skill["source"]
                    and (target / "SKILL.md").is_file()):
                continue
            self.backup_path(target, move=True)
            self.run(self.skill_command(skill))
            entries = read_json(lock).get("skills", {}) if lock.exists() else {}
            if (not (target / "SKILL.md").is_file()
                    or entries.get(skill["name"], {}).get("source") != skill["source"]):
                raise RuntimeError(f"Skill installation/source verification failed: {skill['name']}")
        for plugin in self.manifest["plugins"]:
            if not update and installed.get(plugin, {}).get("enabled"):
                continue
            self.run(["codex", "plugin", "add", plugin, "--json"])
        installed = self.plugins()
        for plugin in self.manifest["plugins"]:
            if not installed.get(plugin, {}).get("enabled"):
                raise RuntimeError(f"Plugin is not installed and enabled: {plugin}")
        for name in self.manifest["local_skills"]:
            if (self.skills / name).resolve() != (self.root / "skills" / name).resolve():
                raise RuntimeError(f"Local skill link verification failed: {name}")
        report = {
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "repository": str(self.root),
            "plugins": [{"id": name, "version": installed[name].get("version")}
                        for name in self.manifest["plugins"]],
            "upstream_skills": {name: entry for name, entry in read_json(lock)["skills"].items()
                                if name in {s["name"] for s in self.manifest["upstream_skills"]}},
            "backup": str(self.backup) if self.backup else None,
        }
        report_path = self.agents / "bootstrap-result.json"
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Verified configuration. Result: {report_path}")
        print("Start a new Codex session to load the installed configuration.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="install; otherwise preview without writes")
    parser.add_argument("--update", action="store_true", help="refresh managed upstream skills/plugins (requires --apply)")
    args = parser.parse_args()
    if args.update and not args.apply:
        parser.error("--update requires --apply")
    manifest = read_json(ROOT / "bootstrap.json")
    validate(ROOT, manifest)
    home = Path.home()
    codex_home = Path(os.environ.get("CODEX_HOME", str(home / ".codex"))).expanduser().resolve()
    installer = Bootstrap(ROOT, home, codex_home, manifest)
    if not args.apply:
        installer.preview()
        return 0
    for command in ("git", "npx", "codex"):
        if shutil.which(command) is None:
            parser.error(f"Required command not found: {command}")
    try:
        installer.apply(update=args.update)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Installation stopped: {error}")
        print("Completed steps remain installed; rerun after fixing the error.")
        if installer.backup:
            print(f"Previous files are recoverable from: {installer.backup}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
