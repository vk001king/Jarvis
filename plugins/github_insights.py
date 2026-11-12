"""Read-only repository analysis tools for GitHub."""
from __future__ import annotations

import urllib.parse

from plugins._github_core import (
    GitHubError,
    api_request,
    get_token,
    page_size,
    repo_path,
    shorten,
)


def _repository(parameters: dict) -> tuple[str, dict]:
    path = repo_path(parameters.get("owner", ""), parameters.get("repository", ""))
    repo, _ = api_request(path)
    if not isinstance(repo, dict):
        raise GitHubError("GitHub did not return repository metadata.")
    return path, repo


def run(parameters: dict, player=None, session_memory=None) -> str:
    params = parameters or {}
    action = str(params.get("action", "summary")).strip().lower()
    if action not in {
        "summary", "languages", "contributors", "branches", "file_tree",
        "compare", "commit_activity",
    }:
        return (
            f"Unknown GitHub Insights action '{action}'. Use summary, languages, "
            "contributors, branches, file_tree, compare, or commit_activity."
        )
    if not get_token():
        return "GitHub token is not configured. Set it in JARVIS plugin settings and press TEST TOKEN."

    try:
        path, repo = _repository(params)

        if action == "summary":
            languages, _ = api_request(f"{path}/languages")
            top_languages = sorted(
                languages.items() if isinstance(languages, dict) else [],
                key=lambda pair: pair[1],
                reverse=True,
            )[:5]
            language_text = ", ".join(name for name, _ in top_languages) or "not detected"
            topics = repo.get("topics") or []
            topic_text = ", ".join(topics[:8]) if topics else "none listed"
            return (
                f"{repo.get('full_name')} · {repo.get('description') or 'No description'}\n"
                f"Default branch: {repo.get('default_branch', 'unknown')} · "
                f"Primary languages: {language_text}\n"
                f"Stars: {repo.get('stargazers_count', 0)} · Forks: {repo.get('forks_count', 0)} · "
                f"Open issues: {repo.get('open_issues_count', 0)}\n"
                f"Topics: {topic_text}\n{repo.get('html_url', '')}"
            )

        if action == "languages":
            languages, _ = api_request(f"{path}/languages")
            if not isinstance(languages, dict) or not languages:
                return "No language statistics are available for this repository."
            total = sum(languages.values())
            return "\n".join(
                f"{name}: {size:,} bytes ({size / total:.1%})"
                for name, size in sorted(languages.items(), key=lambda item: item[1], reverse=True)
            )

        if action == "contributors":
            contributors, _ = api_request(
                f"{path}/contributors",
                params={"per_page": page_size(params, default=10, maximum=30)},
            )
            if not isinstance(contributors, list):
                return "Contributor data is not available."
            return "\n".join(
                f"@{person.get('login', 'unknown')} · "
                f"{person.get('contributions', 0)} contributions"
                for person in contributors
            ) or "No contributors found."

        if action == "branches":
            branches, _ = api_request(
                f"{path}/branches",
                params={"per_page": page_size(params, default=20, maximum=30)},
            )
            if not isinstance(branches, list):
                return "Branch data is not available."
            return "\n".join(
                f"{branch.get('name')} · "
                f"{'protected' if branch.get('protected') else 'unprotected'}"
                for branch in branches
            ) or "No branches found."

        if action == "file_tree":
            branch = str(params.get("branch", "")).strip() or repo.get("default_branch", "main")
            encoded_ref = urllib.parse.quote(branch, safe="")
            commit, _ = api_request(f"{path}/commits/{encoded_ref}")
            tree_sha = commit.get("commit", {}).get("tree", {}).get("sha")
            if not tree_sha:
                return f"Could not resolve the tree for branch '{branch}'."
            tree, _ = api_request(
                f"{path}/git/trees/{urllib.parse.quote(tree_sha, safe='')}",
                params={"recursive": "1"},
            )
            entries = tree.get("tree", []) if isinstance(tree, dict) else []
            if not entries:
                return "No repository tree entries were returned."
            files = [entry for entry in entries if entry.get("type") == "blob"]
            folders = [entry for entry in entries if entry.get("type") == "tree"]
            shown = [entry.get("path", "") for entry in entries[:60]]
            result = (
                f"{repo.get('full_name')} · branch {branch}\n"
                f"{len(files)} files and {len(folders)} folders"
                f"{' (tree truncated by GitHub)' if tree.get('truncated') else ''}\n"
                + "\n".join(shown)
            )
            return shorten(result)

        if action == "compare":
            base = str(params.get("base", "")).strip()
            head = str(params.get("head", "")).strip()
            if not base or not head:
                return "Provide both base and head branch names to compare."
            compare_path = (
                f"{path}/compare/{urllib.parse.quote(base, safe='')}..."
                f"{urllib.parse.quote(head, safe='')}"
            )
            comparison, _ = api_request(compare_path)
            file_changes = comparison.get("files", []) or []
            summary = [
                f"{comparison.get('status', 'comparison')} · "
                f"{comparison.get('ahead_by', 0)} ahead / {comparison.get('behind_by', 0)} behind",
                f"{comparison.get('total_commits', 0)} commits · "
                f"{len(file_changes)} files in returned diff",
            ]
            for item in file_changes[:20]:
                summary.append(
                    f"{item.get('status', 'changed')} {item.get('filename')} "
                    f"(+{item.get('additions', 0)} / -{item.get('deletions', 0)})"
                )
            return "\n".join(summary)

        activity, _ = api_request(f"{path}/stats/commit_activity")
        if not isinstance(activity, list) or not activity:
            return "GitHub has no cached weekly commit activity for this repository yet."
        recent = activity[-12:]
        return "\n".join(
            f"Week {week.get('week')}: {week.get('total', 0)} commits"
            for week in recent
        )

    except (GitHubError, ValueError, TypeError) as exc:
        return f"GitHub analysis failed: {exc}"
    except Exception as exc:
        print(f"[GitHubInsights] Request failed for action {action}: {exc}")
        return "GitHub analysis failed unexpectedly. See the local JARVIS log for details."


PLUGIN = {
    "name": "github_insights",
    "description": (
        "Read-only GitHub repository analysis: summarize repository metadata and "
        "languages, inspect contributors and branches, list a repository file tree, "
        "compare two branches, or review recent weekly commit activity."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "summary | languages | contributors | branches | file_tree | compare | commit_activity",
            },
            "owner": {"type": "STRING", "description": "Repository owner or organization"},
            "repository": {"type": "STRING", "description": "Repository name"},
            "branch": {"type": "STRING", "description": "Optional branch for file_tree"},
            "base": {"type": "STRING", "description": "Base branch for compare"},
            "head": {"type": "STRING", "description": "Head branch for compare"},
            "per_page": {"type": "INTEGER", "description": "Maximum contributor/branch results (1-30)"},
        },
        "required": ["action"],
    },
    "handler": run,
}
