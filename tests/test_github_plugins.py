import io
import json
import unittest
import urllib.error
from unittest.mock import patch

from plugins import _github_core, github, github_insights


class _FakeResponse:
    def __init__(self, value, headers=None):
        self._body = json.dumps(value).encode("utf-8")
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, size=-1):
        return self._body if size < 0 else self._body[:size]


class GitHubPluginTests(unittest.TestCase):
    def test_test_token_uses_authenticated_profile_without_exposing_token(self):
        token = "ghp_test_token_value"
        response = _FakeResponse(
            {"login": "student"},
            {"X-OAuth-Scopes": "repo"},
        )
        with patch.object(_github_core.urllib.request, "urlopen", return_value=response) as urlopen:
            ok, message = _github_core.test_connection({"token": token})

        self.assertTrue(ok)
        self.assertIn("@student", message)
        self.assertNotIn(token, message)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), f"Bearer {token}")
        self.assertEqual(request.full_url, "https://api.github.com/user")

    def test_test_token_reports_auth_failure_without_echoing_secret(self):
        token = "ghp_invalid_secret"
        error = urllib.error.HTTPError(
            "https://api.github.com/user",
            401,
            "Unauthorized",
            {},
            io.BytesIO(b'{"message": "Bad credentials"}'),
        )
        with patch.object(_github_core.urllib.request, "urlopen", side_effect=error):
            ok, message = _github_core.test_connection({"token": token})

        self.assertFalse(ok)
        self.assertIn("Invalid or expired token", message)
        self.assertNotIn(token, message)

    def test_repository_path_rejects_path_injection(self):
        with self.assertRaises(ValueError):
            _github_core.repo_path("../owner", "repo")
        with self.assertRaises(ValueError):
            _github_core.repo_path("owner", "repo/other")

    def test_github_plugin_does_not_make_requests_without_a_token(self):
        with patch.object(github, "get_token", return_value=""), \
             patch.object(github, "api_request") as api_request:
            result = github.run({"action": "profile"})

        self.assertIn("token is not configured", result)
        api_request.assert_not_called()

    def test_insights_summary_combines_repo_and_language_metadata(self):
        repo = {
            "full_name": "student/project",
            "description": "A learning project",
            "default_branch": "main",
            "stargazers_count": 4,
            "forks_count": 1,
            "open_issues_count": 2,
            "topics": ["education"],
            "html_url": "https://github.com/student/project",
        }
        with patch.object(github_insights, "get_token", return_value="configured"), \
             patch.object(
                 github_insights,
                 "api_request",
                 side_effect=[(repo, {}), ({"Python": 1000, "HTML": 200}, {})],
             ):
            result = github_insights.run({
                "action": "summary",
                "owner": "student",
                "repository": "project",
            })

        self.assertIn("student/project", result)
        self.assertIn("Python", result)
        self.assertIn("education", result)


if __name__ == "__main__":
    unittest.main()
