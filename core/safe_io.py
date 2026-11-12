"""
core/safe_io.py — JSON files that survive a crash, a full disk and a bad edit.

WHY THIS EXISTS
    Two files hold everything the user cannot easily recreate: the config with
    the API key and plugin tokens, and the long-term memory. Both used to be
    saved with ``path.write_text(json.dumps(...))``, which truncates the file
    first and writes second. Lose power, kill the process or fill the disk
    between those two steps and the file is empty.

    The read side then made it permanent. Every setter did

        try:    data = json.loads(path.read_text())
        except: data = {}
        data[key] = value
        path.write_text(json.dumps(data))

    so the first setting changed after a damaged read wrote ``{key: value}``
    over what was left — the API key, every plugin token and every stored
    memory gone, with nothing printed anywhere.

WHAT IS DIFFERENT HERE
    * ``write_json`` writes a temporary file beside the target and renames it
      over the original. A rename is atomic: readers see the old file or the
      new one, never half of either.
    * ``read_json_for_update`` tells "there is no file yet" apart from "there
      is a file and it cannot be read". The second case is copied aside before
      anything is written, so the contents stay recoverable by hand.
    * Saved files are made private to the current user where the OS supports
      it, because both of them hold secrets.

Standard library only, and nothing here raises for a reason the caller could
not have had before.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from pathlib import Path

# Windows refuses to rename over a file another handle has open — an antivirus
# scan or a reader on another thread is enough. Those holds last milliseconds,
# so a few short retries turn a spurious failure into a save.
_REPLACE_ATTEMPTS = 5
_REPLACE_PAUSE = 0.05


def _log(msg: str) -> None:
    try:
        print(msg)
    except Exception:
        pass


def quarantine(path: Path) -> Path | None:
    """Copy an unreadable file aside and return where it went.

    A copy rather than a move: if the "corruption" was a transient read error
    the original is still in place for the next attempt. Returns None when
    there was nothing to keep or the copy itself failed."""
    path = Path(path)
    try:
        if not path.exists() or path.stat().st_size == 0:
            return None
        stamp = time.strftime("%Y%m%d-%H%M%S")
        dest = path.with_name(f"{path.name}.corrupt-{stamp}")
        n = 1
        while dest.exists():
            dest = path.with_name(f"{path.name}.corrupt-{stamp}-{n}")
            n += 1
        shutil.copy2(path, dest)
        _make_private(dest)
        return dest
    except Exception as e:
        _log(f"[SafeIO] ⚠️ Could not set aside {path.name}: {e}")
        return None


def read_json(path: Path, default=None):
    """Parse a JSON file for reading only. Returns ``default`` when the file is
    missing or unreadable; never raises and never modifies anything."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def read_json_for_update(path: Path, label: str = "") -> dict:
    """Load a JSON object that is about to be modified and written back.

    Missing file → ``{}``, which is the normal first run. A file that exists
    but does not hold a JSON object is set aside with ``quarantine`` first, so
    the write that follows cannot be the thing that destroys it."""
    path = Path(path)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        problem = "it does not contain a JSON object"
    except Exception as e:
        problem = str(e)

    kept = quarantine(path)
    name = label or path.name
    if kept is not None:
        _log(f"[SafeIO] ⚠️ {name} could not be read ({problem}). "
             f"The old contents were kept as {kept.name}.")
    else:
        _log(f"[SafeIO] ⚠️ {name} could not be read ({problem}).")
    return {}


def _make_private(path: Path) -> None:
    """Owner read/write only. Meaningful on macOS and Linux; on Windows the
    call only toggles the read-only bit and the user profile ACL does the real
    work, so a failure here is never worth reporting."""
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass


def write_json(path: Path, data, *, indent: int = 2, ensure_ascii: bool = True,
               private: bool = True) -> None:
    """Serialise ``data`` and replace ``path`` with it in one atomic step.

    The data is serialised before anything touches the disk, so a value that
    cannot be encoded raises with the existing file untouched."""
    path = Path(path)
    text = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent),
                                    prefix=f"{path.name}.", suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass          # some network and FUSE mounts do not support it
        if private:
            _make_private(tmp)

        for attempt in range(_REPLACE_ATTEMPTS):
            try:
                os.replace(tmp, path)
                return
            except PermissionError:
                time.sleep(_REPLACE_PAUSE * (attempt + 1))

        # Something is holding the file open and is not letting go. Saving in
        # place is what this function replaced, and it is still better than
        # losing the change: the data is already known to serialise, so the
        # window in which the file is incomplete is one short write.
        _log(f"[SafeIO] ⚠️ {path.name} is locked by another program — "
             f"saved in place instead of atomically.")
        path.write_text(text, encoding="utf-8")
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass
