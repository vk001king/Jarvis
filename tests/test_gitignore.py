import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Paths that hold credentials or personal data. None of them may ever be
# offered to `git add`.
MUST_BE_IGNORED = (
    "config/api_keys.json",
    "config/api_keys.json.corrupt-20260101-000000",
    "config/mcp_servers.json",
    "config/certs/jarvis.key",
    "config/certs/jarvis.crt",
    "config/whatsapp_web/session",
    "plugins/token_gmail.json",
    "plugins/client_secret_123.json",
    "google_credentials.json",
    ".env",
    ".env.local",
    "memory/long_term.json",
    "memory/long_term.json.corrupt-20260101-000000",
)


class GitignoreTests(unittest.TestCase):
    def test_no_rule_carries_a_trailing_comment(self):
        # git reads "#" as a comment only at the start of a line. Written after
        # a pattern it becomes part of the pattern, and the rule silently
        # matches nothing — which is how the secrets section once ignored none
        # of the files it listed.
        offenders = [
            line for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#") and " #" in line
        ]
        self.assertEqual(offenders, [])

    def test_git_ignores_every_secret_path(self):
        git = shutil.which("git")
        if not git or not (ROOT / ".git").exists():
            self.skipTest("needs git and a checkout")
        result = subprocess.run(
            [git, "check-ignore", "--no-index", *MUST_BE_IGNORED],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        ignored = set(result.stdout.split())
        self.assertEqual(sorted(set(MUST_BE_IGNORED) - ignored), [])


if __name__ == "__main__":
    unittest.main()
