import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
INCREMENT = ROOT / "ci/increment-runner-revision.py"
CHECK = ROOT / "ci/check-actions-runner-pw.sh"


class IncrementRevisionTest(unittest.TestCase):
    def increment(self, images):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matrix.json"
            original = json.dumps(images, indent=2) + "\n"
            path.write_text(original)
            result = subprocess.run(
                ["python3", str(INCREMENT), str(path)], capture_output=True, text=True
            )
            return result, json.loads(path.read_text()), original == path.read_text()

    def test_increments_only_runner_revision(self):
        images = json.loads((ROOT / "ci/matrix.json").read_text())
        expected = json.loads(json.dumps(images))
        prefix, revision = images[0]["build"]["tag"].rsplit("-", 1)
        expected[0]["build"]["tag"] = f"{prefix}-{int(revision) + 1}"
        result, actual, _ = self.increment(images)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(actual, expected)
        self.assertEqual(result.stdout.strip(), expected[0]["build"]["tag"])

    def test_carries_revision_without_changing_playwright(self):
        images = [{"name": "actions-runner-pw", "build": {"tag": "26-1.65.0-9"}}]
        result, actual, _ = self.increment(images)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(actual[0]["build"]["tag"], "26-1.65.0-10")

    def test_rejects_missing_or_duplicate_runner_without_writing(self):
        runner = {"name": "actions-runner-pw", "build": {"tag": "26-1.65.0-1"}}
        for images in ([], [runner, runner]):
            with self.subTest(images=images):
                result, _, unchanged = self.increment(images)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(unchanged)

    def test_rejects_invalid_tags_without_writing(self):
        for tag in ("latest", "26-1.65.0", "26-1.65.0-x", "26-1.65.0--1", "26-1.65.0-01"):
            with self.subTest(tag=tag):
                result, _, unchanged = self.increment(
                    [{"name": "actions-runner-pw", "build": {"tag": tag}}]
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(unchanged)


class RunnerCheckTest(unittest.TestCase):
    def check(self, missing=None, broken=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binaries = root / "bin"
            browsers = root / "browsers"
            binaries.mkdir()
            browsers.mkdir()
            for name in ("Runner.Listener", "node", "pnpm", "chrome", "firefox"):
                if name == missing:
                    continue
                path = (browsers if name in ("chrome", "firefox") else binaries) / name
                path.write_text("#!/bin/sh\n" + ("exit 1\n" if name == broken else "echo version\n"))
                path.chmod(0o755)
            env = dict(os.environ, PATH=f"{binaries}:{os.environ['PATH']}")
            return subprocess.run(
                ["bash", str(CHECK), str(binaries / "Runner.Listener"), str(browsers)],
                env=env, capture_output=True, text=True,
            )

    def test_checks_all_tools(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("version"), 5)

    def test_rejects_missing_browser(self):
        for name in ("chrome", "firefox"):
            with self.subTest(name=name):
                self.assertNotEqual(self.check(missing=name).returncode, 0)

    def test_rejects_broken_tools_and_browsers(self):
        for name in ("Runner.Listener", "node", "pnpm", "chrome", "firefox"):
            with self.subTest(name=name):
                self.assertNotEqual(self.check(broken=name).returncode, 0)


if __name__ == "__main__":
    unittest.main()
