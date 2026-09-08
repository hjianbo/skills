from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("bootstrap", ROOT / "bootstrap.py")
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / "home"
        self.repo = self.base / "checkout"
        (self.repo / "global").mkdir(parents=True)
        (self.repo / "global/AGENTS.md").write_text("personal rules\n")
        local = self.repo / "skills/local-skill"
        local.mkdir(parents=True)
        (local / "SKILL.md").write_text("local instructions\n")
        self.manifest = {
            "schema_version": 1,
            "skills_cli_version": "1.5.24",
            "local_skills": ["local-skill"],
            "upstream_skills": [{"name": "remote-skill", "source": "owner/repo"}],
            "plugins": ["example@openai-curated-remote"],
        }
        self.calls = []
        self.installed = {}
        self.fail = None
        self.installer = bootstrap.Bootstrap(
            self.repo, self.home, self.home / ".codex", self.manifest, self.run_command
        )

    def run_command(self, command):
        self.calls.append(command)
        if command[:3] == ["codex", "plugin", "list"]:
            return json.dumps({"installed": list(self.installed.values())})
        if command[0] == "npx":
            if self.fail == "skill":
                raise RuntimeError("simulated download failure")
            name = command[command.index("--skill") + 1]
            source = command[command.index("add") + 1]
            target = self.home / ".agents/skills" / name
            target.mkdir(parents=True, exist_ok=True)
            (target / "SKILL.md").write_text("upstream instructions\n")
            lock = self.home / ".agents/.skill-lock.json"
            state = bootstrap.read_json(lock) if lock.exists() else {"skills": {}}
            state["skills"][name] = {"source": source, "skillFolderHash": "fixture-hash"}
            lock.write_text(json.dumps(state))
            return "installed"
        if command[:3] == ["codex", "plugin", "add"]:
            if self.fail != "plugin":
                self.installed[command[3]] = {
                    "pluginId": command[3], "enabled": True, "version": "1.2.3"
                }
            return "{}"
        self.fail_command(command)

    def fail_command(self, command):
        raise AssertionError(f"Unexpected command: {command}")

    def apply(self, update=False):
        with redirect_stdout(io.StringIO()):
            self.installer.apply(update=update)

    def test_preview_does_not_write_or_invoke_installers(self):
        with redirect_stdout(io.StringIO()):
            self.installer.preview()
        self.assertFalse(self.home.exists())
        self.assertEqual(self.calls, [])

    def test_clean_install_and_repeated_run(self):
        bootstrap.validate(self.repo, self.manifest)
        self.apply()
        self.assertEqual((self.home / ".codex/AGENTS.md").read_text(), "personal rules\n")
        self.assertEqual((self.home / ".agents/skills/local-skill").resolve(),
                         self.repo / "skills/local-skill")
        report = bootstrap.read_json(self.home / ".agents/bootstrap-result.json")
        self.assertEqual(report["plugins"][0]["version"], "1.2.3")
        self.assertEqual(report["upstream_skills"]["remote-skill"]["source"], "owner/repo")
        self.calls.clear()
        self.apply()
        self.assertTrue(all(c[:3] == ["codex", "plugin", "list"] for c in self.calls))

    def test_conflicts_backed_up_and_unrelated_data_retained(self):
        agents = self.home / ".agents"
        agents.mkdir(parents=True)
        (agents / "AGENTS.md").write_text("old rules")
        unrelated = agents / "skills/unrelated"
        unrelated.mkdir(parents=True)
        (unrelated / "SKILL.md").write_text("keep")
        config = self.home / ".codex/config.toml"
        config.parent.mkdir()
        config.write_text('model = "custom"\n')
        (agents / ".skill-lock.json").write_text(json.dumps({
            "skills": {"unrelated": {"source": "other/repo"}}
        }))
        self.apply()
        self.assertEqual(config.read_text(), 'model = "custom"\n')
        self.assertEqual((unrelated / "SKILL.md").read_text(), "keep")
        self.assertIn("unrelated", bootstrap.read_json(agents / ".skill-lock.json")["skills"])
        saved = list(self.installer.backup.glob("*/AGENTS.md"))
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].read_text(), "old rules")

    def test_failed_download_retains_backup_and_can_resume(self):
        old = self.home / ".agents/skills/remote-skill"
        old.mkdir(parents=True)
        (old / "SKILL.md").write_text("old skill")
        self.fail = "skill"
        with self.assertRaisesRegex(RuntimeError, "download failure"):
            self.apply()
        saved = list(self.installer.backup.glob("*/remote-skill/SKILL.md"))
        self.assertEqual(saved[0].read_text(), "old skill")
        self.assertFalse((self.home / ".agents/bootstrap-result.json").exists())
        self.fail = None
        self.apply()
        self.assertTrue((old / "SKILL.md").is_file())

    def test_plugin_success_output_requires_installed_state(self):
        self.fail = "plugin"
        with self.assertRaisesRegex(RuntimeError, "not installed and enabled"):
            self.apply()
        self.assertFalse((self.home / ".agents/bootstrap-result.json").exists())

    def test_update_reinstalls_only_managed_dependencies(self):
        self.apply()
        self.calls.clear()
        self.installer = bootstrap.Bootstrap(
            self.repo, self.home, self.home / ".codex", self.manifest, self.run_command
        )
        self.apply(update=True)
        self.assertEqual(sum(c[0] == "npx" for c in self.calls), 1)
        self.assertEqual(sum(c[:3] == ["codex", "plugin", "add"] for c in self.calls), 1)

    def test_custom_codex_directory(self):
        self.installer.codex_home = self.base / "custom-codex"
        self.apply()
        self.assertEqual((self.base / "custom-codex/AGENTS.md").read_text(), "personal rules\n")

    def test_symlinked_config_backup_preserves_original_contents(self):
        config = self.home / ".codex/config.toml"
        config.parent.mkdir(parents=True)
        original = self.base / "config.toml"
        original.write_text('model = "original"\n')
        config.symlink_to(original)
        self.apply()
        original.write_text('model = "changed"\n')
        saved = list(self.installer.backup.glob("*/config.toml"))
        self.assertEqual(saved[0].read_text(), 'model = "original"\n')

    def test_failed_update_does_not_leave_stale_success_report(self):
        self.apply()
        self.installer = bootstrap.Bootstrap(
            self.repo, self.home, self.home / ".codex", self.manifest, self.run_command
        )
        self.fail = "skill"
        with self.assertRaisesRegex(RuntimeError, "download failure"):
            self.apply(update=True)
        self.assertFalse((self.home / ".agents/bootstrap-result.json").exists())

    def test_manifest_cannot_escape_skill_directory(self):
        self.manifest["local_skills"] = ["../outside"]
        with self.assertRaisesRegex(ValueError, "Invalid skill name"):
            bootstrap.validate(self.repo, self.manifest)


if __name__ == "__main__":
    unittest.main()
