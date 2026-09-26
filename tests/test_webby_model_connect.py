import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/webby-model-connect"
loader = importlib.machinery.SourceFileLoader("webby_connect", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
connect = importlib.util.module_from_spec(spec)
loader.exec_module(connect)


class ConnectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root, self.target, self.config = connect.initialize(Path(self.temp.name) / "models")

    def test_init_preserves_owner_configuration_and_is_private(self):
        self.config["providers"]["codex"]["default_model"] = "owner-selection"
        connect.write_private(self.target, json.dumps(self.config))
        _, _, again = connect.initialize(self.root)
        self.assertEqual(again["providers"]["codex"]["default_model"], "owner-selection")
        self.assertEqual(self.root.stat().st_mode & 0o777, 0o700)
        self.assertEqual(self.target.stat().st_mode & 0o777, 0o600)

    def test_rejects_repository_and_symlink_storage(self):
        repo = Path(self.temp.name) / "site"
        (repo / ".git").mkdir(parents=True)
        with self.assertRaises(ValueError):
            connect.initialize(repo / "keys")
        link = Path(self.temp.name) / "link"
        link.symlink_to(self.root)
        with self.assertRaises(ValueError):
            connect.initialize(link)

    def test_rejects_public_existing_state(self):
        self.root.chmod(0o755)
        with self.assertRaises(ValueError):
            connect.initialize(self.root)

    def test_config_updates_merge_after_two_prompts(self):
        stale = json.loads(self.target.read_text())
        connect.save_key(self.root, self.target, self.config, "openai", "fake-openai-key")
        connect.save_key(self.root, self.target, stale, "gemini", "fake-gemini-key")
        data = json.loads(self.target.read_text())
        for name, key in (("openai", "fake-openai-key"), ("gemini", "fake-gemini-key")):
            path = Path(data["providers"][name]["api_key_file"])
            self.assertEqual(path.read_text().strip(), key)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertNotIn(key, self.target.read_text())
            self.assertNotIn("api_key_env", data["providers"][name])

    def test_key_validation_does_not_overwrite(self):
        before = self.target.read_text()
        for name, key in (("codex", "fake"), ("../escape", "fake"), ("openai", "bad\nkey")):
            with self.assertRaises(ValueError):
                connect.save_key(self.root, self.target, self.config, name, key)
        self.assertEqual(before, self.target.read_text())

    def test_subscription_environment_excludes_alternate_billing_and_other_secrets(self):
        environment = {"PATH": "/usr/bin", "HOME": self.temp.name, "CODEX_CA_CERTIFICATE": "/ca.pem",
                       "GH_TOKEN": "fake", "PLOW_AGENT_TOKEN": "fake", "ANTHROPIC_API_KEY": "fake",
                       "CLAUDE_CODE_USE_BEDROCK": "1", "CLAUDE_CODE_OAUTH_TOKEN": "fake"}
        with patch.dict(os.environ, environment, clear=True):
            env = connect.login_env(self.root, "claude")
        self.assertEqual(env["CODEX_CA_CERTIFICATE"], "/ca.pem")
        self.assertEqual(env["HOME"], self.temp.name)
        for name in ("GH_TOKEN", "PLOW_AGENT_TOKEN", "ANTHROPIC_API_KEY", "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_OAUTH_TOKEN"):
            self.assertNotIn(name, env)

    def test_status_requires_subscription_auth(self):
        for provider, output in (("codex", b"Logged in using an API key"),
                                 ("claude", b'{"loggedIn":true,"authMethod":"third_party"}')):
            with patch.object(connect.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, output, b"")):
                self.assertFalse(connect.connected(self.root, provider))
        for provider, output in (("codex", b"Logged in using ChatGPT"),
                                 ("claude", b'{"loggedIn":true,"authMethod":"claude.ai"}')):
            with patch.object(connect.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, output, b"")):
                self.assertTrue(connect.connected(self.root, provider))

    def test_device_status_only_exposes_short_code_and_official_url(self):
        import time
        connect.write_private(self.root / "codex-login.json", json.dumps({"pid": os.getpid(), "started": time.time()}))
        connect.write_private(self.root / "codex-login.log", "secret=fake-secret https://untrusted.example/\nhttps://auth.openai.com/codex/device\nABCD-EFGH\n")
        with patch.object(connect, "connected", return_value=False):
            result = connect.device_status(self.root)
        self.assertEqual(result["user_code"], "ABCD-EFGH")
        self.assertEqual(result["verification_url"], "https://auth.openai.com/codex/device")
        self.assertNotIn("fake-secret", json.dumps(result))
        self.assertNotIn("untrusted", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
