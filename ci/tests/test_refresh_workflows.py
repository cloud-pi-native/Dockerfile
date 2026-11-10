"""Workflow contract tests. Requires PyYAML (python3 -m pip install PyYAML)."""

import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[2]


def load(name):
    path = ROOT / ".github/workflows" / name
    return yaml.load(path.read_text(), Loader=yaml.BaseLoader) if path.exists() else {}


def expression(value, **context):
    code = value.removeprefix("${{").removesuffix("}} ").removesuffix("}}")
    code = code.replace("&&", " and ").replace("||", " or ")
    code = re.sub(r"!(?!=)", "not ", code)
    return eval(code, {"__builtins__": {}, "contains": lambda a, b: b in a, "fromJson": json.loads}, context)


class RefreshWorkflowTest(unittest.TestCase):
    def test_weekly_and_manual_refresh_is_serialized(self):
        workflow = load("refresh-runner.yml")
        self.assertIn("schedule", workflow.get("on", {}))
        self.assertIn("workflow_dispatch", workflow["on"])
        self.assertEqual(workflow["concurrency"]["cancel-in-progress"], "false")
        self.assertEqual(workflow["permissions"]["packages"], "write")
        self.assertEqual(workflow["permissions"]["contents"], "read")

    def test_bump_pushes_main_and_build_uses_exact_commit(self):
        jobs = load("refresh-runner.yml").get("jobs", {})
        self.assertIn("revision", jobs)
        revision = jobs["revision"]
        self.assertEqual(revision["permissions"]["contents"], "write")
        self.assertEqual(revision["steps"][0]["with"]["ref"], "main")
        commands = "\n".join(step.get("run", "") for step in revision["steps"])
        self.assertIn("ci/increment-runner-revision.py", commands)
        self.assertIn("git push origin HEAD:main", commands)
        self.assertIn("Generated with AI assistance, reviewed by @stephanetrebel", commands)
        build = jobs["build"]
        self.assertEqual(build["uses"], "./.github/workflows/build.yml")
        self.assertEqual(build["with"]["REF"], "${{ needs.revision.outputs.ref }}")
        self.assertEqual(build["with"]["IMAGES"], "actions-runner-pw")
        for name in ("BUILD_AMD64", "BUILD_ARM64", "VERIFY_RUNNER", "FORCE_REBUILD"):
            self.assertEqual(build["with"][name], "true")
        self.assertEqual(build["with"]["USE_QEMU"], "false")

    def test_reusable_build_defaults_preserve_existing_calls(self):
        workflow = load("build.yml")
        inputs = workflow["on"]["workflow_call"]["inputs"]
        for name in ("FORCE_REBUILD", "VERIFY_RUNNER"):
            self.assertIn(name, inputs)
            self.assertEqual(inputs[name]["default"], "false")
        for job in ("infos", "build"):
            for step in workflow["jobs"][job]["steps"]:
                if step.get("uses", "").startswith("actions/checkout@"):
                    self.assertEqual(step["with"]["ref"], "${{ inputs.REF }}")
        for job in ("build", "merge"):
            status = next(step for step in workflow["jobs"][job]["steps"] if step.get("id") == "image-status")
            self.assertIn("FORCE_REBUILD", status.get("env", {}))
            self.assertIn('"NEEDS_BUILD=true"', status["run"])

    def test_pull_and_verify_before_exporting_digest(self):
        steps = load("build.yml")["jobs"]["build"]["steps"]
        build = next(step for step in steps if step.get("id") == "build")
        self.assertEqual(build["with"].get("pull"), "true")
        checks = [step for step in steps if "ci/check-actions-runner-pw.sh" in step.get("run", "")]
        self.assertEqual(len(checks), 1)
        check = checks[0]
        self.assertIn("inputs.VERIFY_RUNNER", check["if"])
        self.assertIn("docker run", check["run"])
        self.assertIn("@${{ steps.build.outputs.digest }}", check["env"]["IMAGE"])
        self.assertLess(steps.index(check), next(i for i, step in enumerate(steps) if step.get("name") == "Export digest"))

    def test_status_checks_preserve_skips_and_can_force_new_revision(self):
        for job in ("build", "merge"):
            status = next(step for step in load("build.yml")["jobs"][job]["steps"] if step.get("id") == "image-status")
            for force, http, archs, amd, arm, expected in (
                ("true", "401", [], True, True, "true"),
                ("false", "404", [], True, True, "true"),
                ("false", "200", ["amd64", "arm64"], True, True, "false"),
                ("false", "200", ["amd64"], True, True, "true"),
                ("false", "200", ["arm64"], True, True, "true"),
                ("false", "200", ["amd64"], True, False, "false"),
                ("false", "200", ["arm64"], False, True, "false"),
            ):
                with self.subTest(job=job, force=force, archs=archs, amd=amd, arm=arm):
                    with tempfile.TemporaryDirectory() as directory:
                        root = Path(directory)
                        curl = root / "curl"
                        curl.write_text('#!/bin/bash\nif [[ "$FORCE_REBUILD" == true ]]; then exit 99; fi\nif [[ "$*" == *--head* ]]; then printf "%s" "$HTTP"; else printf "%s" "$MANIFEST"; fi\n')
                        curl.chmod(0o755)
                        output = root / "output"
                        env = dict(os.environ, PATH=f"{root}:{os.environ['PATH']}",
                                   GITHUB_OUTPUT=str(output), FORCE_REBUILD=force,
                                   HTTP=http, MANIFEST=json.dumps({"manifests": [{"platform": {"architecture": arch}} for arch in archs]}),
                                   BUILD_AMD64=json.dumps(amd), BUILD_ARM64=json.dumps(arm),
                                   REGISTRY="example.test", NAMESPACE="namespace", IMAGE_NAME="runner", IMAGE_TAG="tag", REGISTRY_TOKEN="test")
                        result = subprocess.run(["bash", "-euo", "pipefail", "-c", status["run"]], env=env, capture_output=True, text=True)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual(output.read_text().strip(), f"NEEDS_BUILD={expected}")

    def test_revision_commit_and_push_against_local_remote(self):
        step = next(step for step in load("refresh-runner.yml")["jobs"]["revision"]["steps"] if step.get("id") == "revision")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote, checkout = root / "remote.git", root / "checkout"
            def git(*args, cwd=None):
                return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()
            git("init", "--bare", str(remote))
            git("clone", str(remote), str(checkout))
            git("checkout", "-b", "main", cwd=checkout)
            (checkout / "ci").mkdir()
            for name in ("matrix.json", "increment-runner-revision.py"):
                (checkout / "ci" / name).write_text((ROOT / "ci" / name).read_text())
            git("add", "ci", cwd=checkout)
            git("-c", "user.name=Test", "-c", "user.email=test@example.test", "commit", "-m", "Initial", cwd=checkout)
            git("push", "origin", "main", cwd=checkout)
            output = root / "output"
            result = subprocess.run(["bash", "-euo", "pipefail", "-c", step["run"]], cwd=checkout,
                                    env=dict(os.environ, GITHUB_OUTPUT=str(output)), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            sha = git("rev-parse", "HEAD", cwd=checkout)
            self.assertEqual(git("--git-dir", str(remote), "rev-parse", "main"), sha)
            self.assertIn(f"ref={sha}", output.read_text())
            self.assertEqual(git("diff", "--name-only", "HEAD~", "HEAD", cwd=checkout), "ci/matrix.json")
            message = git("log", "-1", "--format=%B", cwd=checkout)
            self.assertIn("\n\nGenerated with AI assistance, reviewed by @stephanetrebel", message)

    def test_manifest_publication_uses_both_digests_and_all_tags(self):
        merge = load("build.yml")["jobs"]["merge"]
        self.assertIn("build", merge["needs"])
        step = next(step for step in merge["steps"] if step.get("name") == "Create manifest list and push")
        script = step["run"].replace("${{ inputs.REGISTRY }}", "ghcr.io").replace("${{ inputs.NAMESPACE }}", "cloud-pi-native").replace("${{ matrix.images.name }}", "actions-runner-pw")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for digest in ("a" * 64, "b" * 64):
                (root / digest).touch()
            # Put the fake docker outside the digest directory to avoid treating it as an image.
            with tempfile.TemporaryDirectory() as binaries:
                docker = Path(binaries) / "docker"
                docker.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
                docker.chmod(0o755)
                tags = ["ghcr.io/cloud-pi-native/actions-runner-pw:26-1.65.0-2", "ghcr.io/cloud-pi-native/actions-runner-pw:latest"]
                env = dict(os.environ, PATH=f"{binaries}:{os.environ['PATH']}", DOCKER_METADATA_OUTPUT_JSON=json.dumps({"tags": tags}))
                result = subprocess.run(["bash", "-euo", "pipefail", "-c", script], cwd=root, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.splitlines(), ["buildx", "imagetools", "create", "-t", tags[0], "-t", tags[1], *[f"ghcr.io/cloud-pi-native/actions-runner-pw@sha256:{letter * 64}" for letter in ("a", "b")]])

    def test_native_and_qemu_platforms_and_artifact_names(self):
        workflow = load("build.yml")
        job = workflow["jobs"]["build"]
        platform_expression = next(step for step in job["steps"] if step.get("id") == "build")["with"]["platforms"]
        artifact = next(step for step in job["steps"] if step.get("uses", "").startswith("actions/upload-artifact@"))["with"]["name"]
        artifact_expression = "${{" + artifact.rsplit("${{", 1)[1]
        for amd, arm, qemu in ((True, False, False), (False, True, False), (True, True, False), (True, False, True), (False, True, True), (True, True, True)):
            inputs = SimpleNamespace(BUILD_AMD64=amd, BUILD_ARM64=arm, USE_QEMU=qemu)
            runners = expression(job["strategy"]["matrix"]["runners"], inputs=inputs)
            artifacts = []
            platforms = []
            for runner in runners:
                context = dict(inputs=inputs, matrix=SimpleNamespace(runners=runner))
                platforms.append(expression(platform_expression, **context))
                artifacts.append(expression(artifact_expression, **context))
            expected = ["linux/amd64,linux/arm64"] if amd and arm and qemu else (["linux/amd64"] if amd else []) + (["linux/arm64"] if arm else [])
            self.assertEqual(platforms, expected, (amd, arm, qemu))
            self.assertEqual(len(artifacts), len(set(artifacts)))


if __name__ == "__main__":
    unittest.main()
