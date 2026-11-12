"""Shared, bounded GitHub REST API helpers for the GitHub plugins."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

from memory.config_manager import get_plugin_setting


_API_ROOT = "https://api.github.com"
_API_VERSION = "2022-11-28"
_MAX_RESPONSE_BYTES = 2 * 1024 * 1024
_MAX_RESULT_CHARS = 12_000


class GitHubError(RuntimeError):
    """A safe, user-facing GitHub API failure without request credentials."""


def get_token() -> str:
    return (
        str(get_plugin_setting("github", "token", "") or "").strip()
        or os.environ.get("GITHUB_TOKEN", "").strip()
    )


def repo_path(owner: str, repository: str) -> str:
    owner = str(owner or "").strip()
    repository = str(repository or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", owner):
        raise ValueError("Provide a valid GitHub owner name.")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", repository):
        raise ValueError("Provide a valid GitHub repository name.")
    return f"/repos/{urllib.parse.quote(owner, safe='')}/{urllib.parse.quote(repository, safe='')}"


def api_request(path: str, params: dict | None = None, method: str = "GET",
                payload: dict | None = None, token: str = "") -> tuple[object, object]:
    token = (token or get_token()).strip()
    if not token:
        raise GitHubError(
            "GitHub token is not configured. Open JARVIS plugin settings, "
            "enter a token, save it, and use TEST TOKEN."
        )
    if not path.startswith("/") or path.startswith("//") or "://" in path:
        raise ValueError("Invalid GitHub API path.")

    url = _API_ROOT + path
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        method=method.upper(),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": _API_VERSION,
            "User-Agent": "JARVIS-GitHub-Plugin",
            **({"Content-Type": "application/json"} if body is not None else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
            headers = response.headers
    except urllib.error.HTTPError as exc:
        try:
            raw_error = exc.read(4096).decode("utf-8", errors="replace")
            parsed = json.loads(raw_error)
            detail = str(parsed.get("message", "")).strip()
        except (OSError, UnicodeError, json.JSONDecodeError, AttributeError):
            detail = ""
        if exc.code == 401:
            detail = "Invalid or expired token."
        elif exc.code == 403 and not detail:
            detail = "Access denied or API rate limit reached."
        raise GitHubError(f"GitHub API returned HTTP {exc.code}" + (f": {detail}" if detail else ".")) from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise GitHubError(f"Could not reach api.github.com: {exc}") from None

    if len(raw) > _MAX_RESPONSE_BYTES:
        raise GitHubError("GitHub response exceeded the 2 MB safety limit.")
    if not raw:
        return None, headers
    try:
        return json.loads(raw.decode("utf-8")), headers
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise GitHubError(f"GitHub returned an invalid JSON response: {exc}") from None


def test_connection(values: dict | None = None) -> tuple[bool, str]:
    token = str((values or {}).get("token") or get_token()).strip()
    if not token:
        return False, "Enter a GitHub token and save it before testing."
    try:
        profile, headers = api_request("/user", token=token)
    except (GitHubError, ValueError) as exc:
        return False, str(exc)
    if not isinstance(profile, dict) or not profile.get("login"):
        return False, "GitHub responded, but did not return an authenticated account."
    scopes = headers.get("X-OAuth-Scopes", "") if headers else ""
    suffix = f" · scopes: {scopes}" if scopes else ""
    return True, f"Connected as @{profile['login']}{suffix}."


def shorten(value: object, limit: int = _MAX_RESULT_CHARS) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[:limit] + "\n…(truncated)"


def require_repo(parameters: dict) -> str:
    return repo_path(parameters.get("owner", ""), parameters.get("repository", ""))


def page_size(parameters: dict, default: int = 10, maximum: int = 30) -> int:
    try:
        return max(1, min(maximum, int(parameters.get("per_page", default))))
    except (TypeError, ValueError):
        return default
