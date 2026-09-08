import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


SCRIPT = Path(__file__).resolve().parents[1] / "skills/emqx-hot-patch-package/scripts/build_emqx_hot_patch_zip.py"


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.beam = self.root / "example.beam"
        # Opaque bytes test packaging, not Erlang compilation or hot loading.
        self.beam.write_bytes(b"packaging fixture\x00\xff")
        self.output = self.root / "output"

    def run_package(self, name="patch", beams=None, extra=()):
        command = [sys.executable, str(SCRIPT), "--package-name", name,
                   "--output-dir", str(self.output), "--fix-title", "Example fix",
                   "--fix-summary", "Correct example behavior."]
        for beam in beams if beams is not None else [self.beam]:
            command.extend(["--beam", str(beam)])
        # Verify the documented path without optional Erlang metadata extraction.
        return subprocess.run(command + list(extra), capture_output=True, text=True,
                              env={**os.environ, "PATH": ""})

    def test_archive_preserves_bytes_and_reports_hashes(self):
        result = self.run_package()
        self.assertEqual(result.returncode, 0, result.stderr)
        archive = self.output / "patch.zip"
        with zipfile.ZipFile(archive) as zipped:
            self.assertEqual(set(zipped.namelist()), {
                "patch/README.md", "patch/patches/", "patch/patches/example.beam"})
            self.assertEqual(zipped.read("patch/patches/example.beam"), self.beam.read_bytes())
            readme = zipped.read("patch/README.md").decode()
        self.assertTrue(readme.startswith("# Example fix\n"))
        self.assertIn("\n## Build Information\n", readme)
        self.assertNotIn("protocol_violation", readme)
        self.assertNotIn("invalid_sql_statement_name", readme)
        self.assertNotIn("Errors addressed", readme)
        self.assertIn(hashlib.sha256(self.beam.read_bytes()).hexdigest(), readme)
        self.assertIn(hashlib.sha256(archive.read_bytes()).hexdigest(), result.stdout)

    def test_explicit_errors_are_preserved(self):
        result = self.run_package(extra=["--fixed-errors", "timeout", "--fixed-errors", "closed"])
        self.assertEqual(result.returncode, 0, result.stderr)
        readme = (self.output / "patch/README.md").read_text()
        self.assertIn("- `timeout`\n- `closed`", readme)

    def test_existing_directory_is_preserved(self):
        package = self.output / "patch"
        package.mkdir(parents=True)
        marker = package / "keep.txt"
        marker.write_text("existing data")
        result = self.run_package()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(marker.read_text(), "existing data")
        self.assertFalse((self.output / "patch.zip").exists())

    def test_existing_archive_is_preserved(self):
        self.output.mkdir()
        archive = self.output / "patch.zip"
        archive.write_bytes(b"existing archive")
        self.assertNotEqual(self.run_package().returncode, 0)
        self.assertEqual(archive.read_bytes(), b"existing archive")
        self.assertFalse((self.output / "patch").exists())

    def test_path_names_are_rejected_before_writing(self):
        for name in ["..", ".", "../escape", str(self.root / "absolute"), "a/b"]:
            with self.subTest(name=name):
                self.assertNotEqual(self.run_package(name=name).returncode, 0)
                self.assertFalse(self.output.exists())

    def test_invalid_inputs_leave_no_output(self):
        invalid = self.root / "not_a_beam.txt"
        invalid.write_text("input")
        for beam in [invalid, self.root / "missing.beam"]:
            with self.subTest(beam=beam):
                self.assertNotEqual(self.run_package(beams=[self.beam, beam]).returncode, 0)
                self.assertFalse(self.output.exists())

    def test_duplicate_names_are_rejected_before_writing(self):
        other = self.root / "other"
        other.mkdir()
        duplicate = other / self.beam.name
        duplicate.write_bytes(b"different module version")
        self.assertNotEqual(self.run_package(beams=[self.beam, duplicate]).returncode, 0)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
