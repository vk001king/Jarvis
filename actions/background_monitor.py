"""
BackgroundMonitor — user-configured topic watching.
Checks DDG news once per day per topic; alerts JARVIS when a new headline appears.
No crypto, no finance, no uninvited tracking.
"""
import hashlib
import re
from datetime import datetime
from pathlib import Path


# ── Blocked categories (never monitor regardless of what user says) ────────────

_BLOCKED = {
    # Brand / asset names — spelled the same in every language
    "bitcoin", "ethereum", "dogecoin", "solana", "binance",
    "nft", "blockchain", "defi", "altcoin", "memecoin", "coin", "token",
    # spellings of the "crypto" root across different languages
    "crypto", "kripto", "cripto", "krypto", "крипто", "仮想通貨", "暗号資産",
    "cryptocurrency",
}

def _is_blocked(topic: str) -> bool:
    t = topic.lower()
    return any(word in t for word in _BLOCKED)


# ── Slug / hash helpers ────────────────────────────────────────────────────────

def _slug(topic: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", topic.lower().strip())[:40].strip("_")

def _title_hash(title: str) -> str:
    return hashlib.md5(title.encode("utf-8", errors="ignore")).hexdigest()[:12]


# ── Memory I/O ─────────────────────────────────────────────────────────────────

def _load() -> dict:
    from memory.memory_manager import load_memory
    data = load_memory().get("monitors", {})
    return data if isinstance(data, dict) else {}

def _change(edit):
    """Run ``edit(monitors)`` against the stored topics and save, as one step.

    Every change goes through here so the read and the write happen under the
    memory lock. Each function used to load the topics, work on that copy and
    write the whole memory file back — so whatever was saved in between was
    erased: a fact the model stored, or a topic added while the daily check
    was still waiting on the network.

    ``edit`` returns the value to hand back; returning None from it means
    "nothing changed" and skips the write."""
    from memory.memory_manager import mutate_memory

    outcome = None

    def _apply(memory: dict):
        nonlocal outcome
        monitors = memory.get("monitors")
        if not isinstance(monitors, dict):
            monitors = {}
        outcome = edit(monitors)
        if outcome is None:
            return False
        memory["monitors"] = monitors
        return True

    mutate_memory(_apply)
    return outcome


# ── Public API ─────────────────────────────────────────────────────────────────

def add_monitor(topic: str) -> str:
    topic = topic.strip()
    if not topic:
        return "Please specify a topic to monitor."
    if _is_blocked(topic):
        return "I don't monitor crypto or financial topics."
    slug = _slug(topic)
    if not slug:
        # A topic with no Latin letters or digits has no slug to file it under.
        slug = "topic_" + _title_hash(topic)
    existing = _load().get(slug)
    if isinstance(existing, dict):
        return f"Already monitoring: {existing.get('topic', topic)}"

    def _add(monitors: dict):
        if slug in monitors:
            return None
        monitors[slug] = {
            "topic":      topic,
            "added":      datetime.now().strftime("%Y-%m-%d"),
            "last_check": "",
            "last_hash":  "",
        }
        return True

    _change(_add)
    print(f"[Monitor] ➕ Added: {topic}")
    return f"Now monitoring: {topic}"


def remove_monitor(topic: str) -> str:
    topic = topic.strip().lower()
    if not topic:
        return "Please specify which topic to stop monitoring."

    def _label(key: str, val) -> str:
        return str(val.get("topic", key)) if isinstance(val, dict) else key

    def _remove(monitors: dict):
        # exact slug match first
        slug = _slug(topic)
        if slug and slug in monitors:
            return _label(slug, monitors.pop(slug))
        # partial match fallback
        for key, val in list(monitors.items()):
            if topic in _label(key, val).lower():
                return _label(key, monitors.pop(key))
        return None

    label = _change(_remove)
    if label is None:
        return f"Not found in monitored topics: {topic}"
    return f"Stopped monitoring: {label}"


def list_monitors() -> list[str]:
    return [v.get("topic", k) if isinstance(v, dict) else k
            for k, v in _load().items()]


def check_all() -> list[str]:
    """
    Run all pending topic checks (once per day per topic).
    Returns a list of [MONITOR_ALERT] strings — empty if nothing new.
    """
    from actions.web_search import _ddg_news

    monitors = _load()
    if not monitors:
        return []

    today   = datetime.now().strftime("%Y-%m-%d")
    alerts  = []
    # What this run learned, per topic. Applied to the stored topics at the end
    # rather than written back as a whole: the searches below take seconds, and
    # a topic added or removed in that time must survive.
    updates: dict[str, dict] = {}

    for slug, data in monitors.items():
        if not isinstance(data, dict):
            continue                     # not a topic record — leave it alone
        if data.get("last_check") == today:
            continue                     # already checked today

        topic = data.get("topic", slug)
        try:
            results = _ddg_news(topic, max_results=5)
            if not results:
                updates[slug] = {"last_check": today}
                continue

            top   = results[0]
            title = top.get("title", "").strip()
            if not title:
                continue

            h = _title_hash(title)
            updates[slug] = {"last_check": today}

            if h == data.get("last_hash"):
                continue                 # same headline as last check — no alert

            updates[slug]["last_hash"] = h

            snippet = top.get("snippet", "")[:150]
            source  = top.get("source", "")
            parts   = [f"[MONITOR_ALERT] {topic}", f"Headline: {title}"]
            if snippet:
                parts.append(snippet)
            if source:
                parts.append(f"Source: {source}")
            alerts.append("\n".join(parts))
            print(f"[Monitor] 🔔 New headline for '{topic}': {title[:60]}")

        except Exception as e:
            print(f"[Monitor] ⚠️ Check failed for '{topic}': {e}")

    if updates:
        def _stamp(stored: dict):
            touched = None
            for slug, fields in updates.items():
                if isinstance(stored.get(slug), dict):
                    stored[slug].update(fields)
                    touched = True
            return touched

        _change(_stamp)

    return alerts
