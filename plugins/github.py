"""GitHub account and repository operations for JARVIS."""
from __future__ import annotations

import base64
import urllib.parse

from plugins._github_core import (
    GitHubError,
    api_request,
    get_token,
    page_size,
    repo_path,
    shorten,
    test_connection,
)


def _format_repositories(items: list) -> str:
    if not items:
        return "No repositories found."
    lines = []
    for repo in items:
        visibility = "private" if repo.get("private") else "public"
        lines.append(
            f"{repo.get('full_name', repo.get('name', 'repository'))} "
            f"({visibility}) · ★ {repo.get('stargazers_count', 0)} · "
            f"open issues {repo.get('open_issues_count', 0)}"
        )
    return "\n".join(lines)


def run(parameters: dict, player=None, session_memory=None) -> str:
    params = parameters or {}
    action = str(params.get("action", "profile")).strip().lower()

    if action == "test_token":
        return test_connection()[1]
    if action not in {
        "profile", "list_repos", "search_repos", "search_code", "get_repo",
        "list_issues", "create_issue", "list_pull_requests", "get_pull_request",
        "latest_release", "workflow_runs", "commits", "read_file",
    }:
        return f"Unknown GitHub action '{action}'. Use the action list in the plugin description."
    if not get_token():
        return "GitHub token is not configured. Set it in JARVIS plugin settings and press TEST TOKEN."

    try:
        if action == "profile":
            data, _ = api_request("/user")
            return (
                f"GitHub account: @{data.get('login', 'unknown')} · "
                f"{data.get('name') or 'name not set'} · "
                f"{data.get('public_repos', 0)} public repositories · "
                f"{data.get('followers', 0)} followers."
            )

        if action == "list_repos":
            repos, _ = api_request(
                "/user/repos",
                params={
                    "sort": str(params.get("sort", "updated")),
                    "direction": "desc",
                    "per_page": page_size(params),
                    "visibility": "all",
                },
            )
            return _format_repositories(repos if isinstance(repos, list) else [])

        if action in ("search_repos", "search_code"):
            query = str(params.get("query", "")).strip()
            if not query:
                return "Provide a search query."
            endpoint = "repositories" if action == "search_repos" else "code"
            results, _ = api_request(
                f"/search/{endpoint}",
                params={"q": query, "per_page": page_size(params)},
            )
            items = results.get("items", []) if isinstance(results, dict) else []
            if action == "search_repos":
                return _format_repositories(items)
            return "\n".join(
                f"{item.get('repository', {}).get('full_name', '')}: "
                f"{item.get('path', '')} · {item.get('html_url', '')}"
                for item in items
            ) or "No code matches found."

        if action == "get_repo":
            path = repo_path(params.get("owner", ""), params.get("repository", ""))
            repo, _ = api_request(path)
            return (
                f"{repo.get('full_name')} · {repo.get('description') or 'No description'}\n"
                f"Default branch: {repo.get('default_branch', 'unknown')} · "
                f"Language: {repo.get('language') or 'not detected'} · "
                f"★ {repo.get('stargazers_count', 0)} · "
                f"Forks: {repo.get('forks_count', 0)} · "
                f"Open issues: {repo.get('open_issues_count', 0)}\n"
                f"{repo.get('html_url', '')}"
            )

        repo = repo_path(params.get("owner", ""), params.get("repository", ""))
        if action == "list_issues":
            issues, _ = api_request(
                f"{repo}/issues",
                params={
                    "state": str(params.get("state", "open")),
                    "per_page": page_size(params),
                },
            )
            issue_items = [
                item for item in issues
                if isinstance(item, dict) and "pull_request" not in item
            ] if isinstance(issues, list) else []
            return "\n".join(
                f"#{item.get('number')} {item.get('title')} · "
                f"{item.get('state')} · {item.get('html_url')}"
                for item in issue_items
            ) or "No issues found."

        if action == "create_issue":
            title = str(params.get("title", "")).strip()
            if not title:
                return "A title is required to create a GitHub issue."
            labels = params.get("labels", [])
            if isinstance(labels, str):
                labels = [label.strip() for label in labels.split(",") if label.strip()]
            if not isinstance(labels, list) or not all(isinstance(label, str) for label in labels):
                return "Labels must be provided as a list of strings."
            issue, _ = api_request(
                f"{repo}/issues",
                method="POST",
                payload={
                    "title": title[:256],
                    "body": str(params.get("body", ""))[:60_000],
                    "labels": labels[:20],
                },
            )
            return f"Created issue #{issue.get('number')}: {issue.get('html_url')}"

        if action in ("list_pull_requests", "get_pull_request"):
            if action == "list_pull_requests":
                pulls, _ = api_request(
                    f"{repo}/pulls",
                    params={
                        "state": str(params.get("state", "open")),
                        "per_page": page_size(params),
                    },
                )
                return "\n".join(
                    f"#{item.get('number')} {item.get('title')} · "
                    f"{item.get('state')} · {item.get('html_url')}"
                    for item in pulls if isinstance(item, dict)
                ) or "No pull requests found."
            try:
                number = int(params.get("number", 0))
            except (TypeError, ValueError):
                number = 0
            if number <= 0:
                return "Provide a positive pull request number."
            pull, _ = api_request(f"{repo}/pulls/{number}")
            return (
                f"PR #{pull.get('number')} {pull.get('title')} · {pull.get('state')}\n"
                f"Author: {pull.get('user', {}).get('login', 'unknown')} · "
                f"base {pull.get('base', {}).get('ref', '?')} ← "
                f"{pull.get('head', {}).get('ref', '?')}\n"
                f"{pull.get('html_url')}\n"
                f"{shorten(pull.get('body'), 3000)}"
            )

        if action == "latest_release":
            release, _ = api_request(f"{repo}/releases/latest")
            return (
                f"{release.get('name') or release.get('tag_name', 'Latest release')} · "
                f"published {release.get('published_at', 'date unavailable')}\n"
                f"{release.get('html_url')}\n{shorten(release.get('body'), 3000)}"
            )

        if action == "workflow_runs":
            result, _ = api_request(
                f"{repo}/actions/runs",
                params={"per_page": page_size(params)},
            )
            runs = result.get("workflow_runs", []) if isinstance(result, dict) else []
            return "\n".join(
                f"{item.get('name', 'Workflow')} · {item.get('status')} / "
                f"{item.get('conclusion') or 'in progress'} · "
                f"{item.get('html_url')}"
                for item in runs
            ) or "No workflow runs found."

        if action == "commits":
            query = {"per_page": page_size(params)}
            branch = str(params.get("branch", "")).strip()
            if branch:
                query["sha"] = branch
            commits, _ = api_request(f"{repo}/commits", params=query)
            return "\n".join(
                f"{item.get('sha', '')[:8]} · "
                f"{item.get('commit', {}).get('message', '').splitlines()[0]} · "
                f"{item.get('html_url', '')}"
                for item in commits if isinstance(item, dict)
            ) or "No commits found."

        if action == "read_file":
            file_path = str(params.get("path", "")).strip().strip("/")
            if not file_path or ".." in file_path.split("/"):
                return "Provide a valid repository-relative file path."
            ref = str(params.get("ref", "")).strip()
            query = {"ref": ref} if ref else None
            content, _ = api_request(
                f"{repo}/contents/{urllib.parse.quote(file_path, safe='/')}",
                params=query,
            )
            if not isinstance(content, dict) or content.get("encoding") != "base64":
                return "GitHub did not return a readable base64 file."
            decoded = base64.b64decode(content.get("content", "")).decode(
                "utf-8", errors="replace"
            )
            return f"{file_path} ({content.get('size', 0)} bytes):\n{shorten(decoded)}"

    except (GitHubError, ValueError, TypeError) as exc:
        return f"GitHub request failed: {exc}"
    except Exception as exc:
        print(f"[GitHub] Request failed for action {action}: {exc}")
        return "GitHub request failed unexpectedly. See the local JARVIS log for details."

    return "GitHub action was not completed."


def _test_token(values: dict) -> tuple[bool, str]:
    return test_connection(values)


PLUGIN = {
    "name": "github",
    "description": (
        "GitHub assistant for account profile, repository listing/search and details, "
        "code search, reading repository files, issues, pull requests, releases, "
        "commits, and GitHub Actions workflow runs. Can create an issue when explicitly "
        "asked. Use this plugin for GitHub.com operations."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": (
                    "profile | list_repos | search_repos | search_code | get_repo | "
                    "list_issues | create_issue | list_pull_requests | get_pull_request | "
                    "latest_release | workflow_runs | commits | read_file | test_token"
                ),
            },
            "owner": {"type": "STRING", "description": "Repository owner or organization"},
            "repository": {"type": "STRING", "description": "Repository name"},
            "query": {"type": "STRING", "description": "GitHub repository or code search query"},
            "state": {"type": "STRING", "description": "Issue or pull-request state: open, closed, or all"},
            "per_page": {"type": "INTEGER", "description": "Maximum results to return (1-30)"},
            "branch": {"type": "STRING", "description": "Optional branch or commit for commit listing"},
            "number": {"type": "INTEGER", "description": "Issue or pull-request number"},
            "title": {"type": "STRING", "description": "Title for a new issue"},
            "body": {"type": "STRING", "description": "Issue text or body"},
            "labels": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Optional issue labels"},
            "path": {"type": "STRING", "description": "Repository-relative path for read_file"},
            "ref": {"type": "STRING", "description": "Optional branch, tag, or commit for read_file"},
            "sort": {"type": "STRING", "description": "Repository sort: created, updated, pushed, or full_name"},
        },
        "required": ["action"],
    },
    "handler": run,
}


PLUGIN_SETTINGS = {
    "namespace": "github",
    "title": "GitHub connection",
    "fields": [
        {
            "key": "token",
            "label": "Personal access token (stored locally in plaintext)",
            "type": "password",
            "placeholder": "Paste a GitHub token; it will not be shown in logs",
        },
    ],
    "action": {"label": "TEST TOKEN", "run": _test_token},
}
