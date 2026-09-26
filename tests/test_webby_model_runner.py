"""Check that model handoffs stay in the assigned files and leave source untouched."""

import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/webby-model-runner"
loader = importlib.machinery.SourceFileLoader("webby_model_runner", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
runner = importlib.util.module_from_spec(spec)
loader.exec_module(runner)


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True).stdout.strip()


class ModelRunnerTests(unittest.TestCase):
    def test_invalid_scopes_and_agents_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            plan = Path(temp) / "plan.json"
            for scope in ("../secret", "/etc/passwd", "site/../../secret", ".git/config"):
                plan.write_text(json.dumps({"brief": "A real site", "steps": [
                    {"agent": "codex", "task": "Make it", "paths": [scope]}]}))
                with self.subTest(scope=scope), self.assertRaises(runner.RunnerError):
                    runner.load_plan(plan)
            plan.write_text(json.dumps({"brief": "A real site", "steps": [
                {"agent": "unknown", "task": "Make it", "paths": ["site/**"]}]}))
            with self.assertRaises(runner.RunnerError):
                runner.load_plan(plan)

    def test_two_agents_produce_one_patch_without_editing_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            git(repo, "init", "-q")
            (repo / "site").mkdir()
            (repo / "site/index.html").write_text("<h1>Start</h1>\n")
            git(repo, "add", ".")
            git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.com",
                "commit", "-qm", "Initial site")
            baseline = (repo / "site/index.html").read_text()
            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_docker = fake_bin / "docker"
            fake_docker.write_text("""#!/usr/bin/env python3
import pathlib, sys
args = sys.argv[1:]
work_mounts = [args[i + 1] for i, x in enumerate(args) if x == '--mount' and ',dst=/work' in args[i + 1]]
if not work_mounts:
    sys.exit(0)
mount = work_mounts[0]
repo = pathlib.Path(mount.split(',dst=')[0].split('src=')[1])
if 'codex' in args:
    (repo / 'site/index.html').write_text('<h1>Codex</h1>\\n')
else:
    (repo / 'site/faq.html').write_text('<h2>Questions</h2>\\n')
""")
            fake_docker.chmod(0o755)
            plan = root / "plan.json"
            plan.write_text(json.dumps({"brief": "A real site", "steps": [
                {"agent": "codex", "task": "Build a page", "paths": ["site/index.html"]},
                {"agent": "claude", "task": "Add FAQ", "paths": ["site/faq.html"]}]}))
            patch = root / "result.patch"
            env = os.environ.copy()
            env["PATH"] = f"{fake_bin}:{env['PATH']}"
            result = subprocess.run([sys.executable, str(SCRIPT), "--state-dir", str(root / "state"),
                                     "run", str(plan), "--repo", str(repo), "--patch", str(patch)],
                                    text=True, capture_output=True, env=env, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((repo / "site/index.html").read_text(), baseline)
            self.assertFalse((repo / "site/faq.html").exists())
            self.assertIn("site/faq.html", patch.read_text())
            git(repo, "apply", "--check", str(patch))

    def test_out_of_scope_change_blocks_patch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            git(repo, "init", "-q")
            (repo / "site").mkdir()
            (repo / "site/index.html").write_text("<h1>Start</h1>\n")
            git(repo, "add", ".")
            git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.com",
                "commit", "-qm", "Initial site")
            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_docker = fake_bin / "docker"
            fake_docker.write_text("""#!/usr/bin/env python3
import pathlib, sys
args = sys.argv[1:]
work_mounts = [args[i + 1] for i, x in enumerate(args) if x == '--mount' and ',dst=/work' in args[i + 1]]
if not work_mounts:
    sys.exit(0)
mount = work_mounts[0]
repo = pathlib.Path(mount.split(',dst=')[0].split('src=')[1])
(repo / 'site/other.html').write_text('Outside scope\\n')
""")
            fake_docker.chmod(0o755)
            plan = root / "plan.json"
            plan.write_text(json.dumps({"brief": "A real site", "steps": [
                {"agent": "codex", "task": "Build a page", "paths": ["site/index.html"]}]}))
            patch = root / "result.patch"
            env = os.environ.copy()
            env["PATH"] = f"{fake_bin}:{env['PATH']}"
            result = subprocess.run([sys.executable, str(SCRIPT), "--state-dir", str(root / "state"),
                                     "run", str(plan), "--repo", str(repo), "--patch", str(patch)],
                                    text=True, capture_output=True, env=env, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("outside its assigned paths", result.stderr)
            self.assertFalse(patch.exists())
            self.assertFalse((repo / "site/other.html").exists())

    def test_symlink_is_not_accepted_as_website_output(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            git(repo, "init", "-q")
            (repo / "site").mkdir()
            (repo / "site/contact.html").symlink_to("/home/webby/.codex/auth.json")
            git(repo, "add", "-A")
            with self.assertRaisesRegex(runner.RunnerError, "unsupported file type"):
                runner.reject_special_files(repo, ["site/contact.html"])

    def test_doctor_checks_selected_agent_and_codex_sandbox_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_docker = fake_bin / "docker"
            fake_docker.write_text("""#!/usr/bin/env python3
import sys
args = sys.argv[1:]
if 'sandbox' in args:
    sys.exit(1)
sys.exit(0)
""")
            fake_docker.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{fake_bin}:{env['PATH']}"
            base = [sys.executable, str(SCRIPT), "--state-dir", str(root / "state")]
            for agent, expected in (("claude", 0), ("codex", 1)):
                result = subprocess.run(base + ["doctor", agent], text=True,
                                        capture_output=True, env=env, check=False)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            general = subprocess.run(base + ["doctor"], text=True,
                                     capture_output=True, env=env, check=False)
            self.assertEqual(general.returncode, 0, general.stdout + general.stderr)
            self.assertIn("Codex sandbox cannot start", general.stdout)
            repo = root / "repo"
            repo.mkdir()
            git(repo, "init", "-q")
            (repo / "site").mkdir()
            (repo / "site/index.html").write_text("<h1>Start</h1>\n")
            git(repo, "add", ".")
            git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.com",
                "commit", "-qm", "Initial site")
            plan = root / "plan.json"
            plan.write_text(json.dumps({"brief": "A real site", "steps": [
                {"agent": "codex", "task": "Build it", "paths": ["site/**"]}]}))
            patch = root / "result.patch"
            run = subprocess.run(base + ["run", str(plan), "--repo", str(repo), "--patch", str(patch)],
                                 text=True, capture_output=True, env=env, check=False)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("codex is unavailable", run.stderr)
            self.assertFalse(patch.exists())


if __name__ == "__main__":
    unittest.main()
