"""
core/secret_guard.py — recognise machine credentials before they are filed
away as "something to remember".

WHY THIS EXISTS
    save_memory stores whatever the model decides is worth keeping. Say "my
    GitHub token is ghp_…" and the token becomes a memory entry: written to
    memory/long_term.json in plain text, listed in the memory panel, and sent
    back to the cloud model every time recall_memory matches it. None of that
    is what a person means by "use this token".

    Credentials already have a home — the plugin settings panel, which is what
    the plugins actually read — so the right answer is to decline and say where
    it goes.

WHAT IT MATCHES
    Only formats that are unmistakably machine-issued: provider prefixes,
    JSON Web Tokens and PEM private keys. There is deliberately no "the key is
    called password" rule. A person who asks the assistant to remember the
    guest WiFi password has made a choice about their own data, and guessing
    from a name would also swallow harmless facts like
    ``github_token_created = yes``.
"""

from __future__ import annotations

import re

_PATTERNS: tuple[tuple[str, re.Pattern], ...] = (
    ("GitHub token",      re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("GitHub token",      re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b")),
    ("Google API key",    re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("API key",           re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}\b")),
    ("Slack token",       re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}\b")),
    ("AWS access key",    re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitLab token",      re.compile(r"\bglpat-[A-Za-z0-9_\-]{20,}\b")),
    ("Hugging Face token", re.compile(r"\bhf_[A-Za-z0-9]{30,}\b")),
    ("JSON Web Token",    re.compile(
        r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b")),
    ("private key",       re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
)


def find_secret(text) -> str | None:
    """Name the kind of credential found in ``text``, or None."""
    if not isinstance(text, str) or len(text) < 16:
        return None
    for kind, pattern in _PATTERNS:
        if pattern.search(text):
            return kind
    return None


def mask(text) -> str:
    """Replace every recognised credential in ``text`` with a short stub that
    keeps the first four characters, so the user can still tell which one it
    was without the value leaving the machine again."""
    out = str(text or "")
    for _kind, pattern in _PATTERNS:
        out = pattern.sub(lambda m: f"{m.group(0)[:4]}…[hidden]", out)
    return out
