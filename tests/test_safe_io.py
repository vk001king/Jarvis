import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import safe_io


class SafeIoTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.path = self.dir / "store.json"

    def test_write_then_read_round_trips_and_leaves_no_temp_files(self):
        safe_io.write_json(self.path, {"name": "Ayşe", "n": 1}, ensure_ascii=False)

        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")),
                         {"name": "Ayşe", "n": 1})
        self.assertEqual([p.name for p in self.dir.iterdir()], ["store.json"])

    def test_write_creates_missing_parent_directories(self):
        nested = self.dir / "a" / "b" / "store.json"
        safe_io.write_json(nested, {"ok": True})
        self.assertTrue(nested.exists())

    @unittest.skipIf(os.name == "nt", "POSIX permission bits")
    def test_written_file_is_private_to_the_owner(self):
        safe_io.write_json(self.path, {"token": "x"})
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_unserialisable_data_leaves_the_existing_file_untouched(self):
        safe_io.write_json(self.path, {"keep": "me"})
        with self.assertRaises(TypeError):
            safe_io.write_json(self.path, {"bad": object()})

        self.assertEqual(safe_io.read_json(self.path), {"keep": "me"})
        self.assertEqual([p.name for p in self.dir.iterdir()], ["store.json"])

    def test_failed_replace_keeps_the_old_file_and_cleans_up(self):
        safe_io.write_json(self.path, {"keep": "me"})
        with patch.object(safe_io.os, "replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                safe_io.write_json(self.path, {"new": "value"})

        self.assertEqual(safe_io.read_json(self.path), {"keep": "me"})
        self.assertEqual([p.name for p in self.dir.iterdir()], ["store.json"])

    def test_replace_is_retried_when_the_file_is_briefly_locked(self):
        real_replace = os.replace
        calls = []

        def flaky(src, dst):
            calls.append(src)
            if len(calls) < 3:
                raise PermissionError("in use")
            return real_replace(src, dst)

        with patch.object(safe_io.os, "replace", side_effect=flaky), \
                patch.object(safe_io.time, "sleep"):
            safe_io.write_json(self.path, {"saved": True})

        self.assertEqual(len(calls), 3)
        self.assertEqual(safe_io.read_json(self.path), {"saved": True})

    def test_a_file_that_stays_locked_is_still_saved_in_place(self):
        safe_io.write_json(self.path, {"old": True})
        with patch.object(safe_io.os, "replace", side_effect=PermissionError("in use")), \
                patch.object(safe_io.time, "sleep"):
            safe_io.write_json(self.path, {"new": True})

        self.assertEqual(safe_io.read_json(self.path), {"new": True})
        self.assertEqual([p.name for p in self.dir.iterdir()], ["store.json"])

    def test_read_for_update_returns_empty_for_a_missing_file(self):
        self.assertEqual(safe_io.read_json_for_update(self.path), {})
        self.assertEqual(list(self.dir.iterdir()), [])

    def test_read_for_update_sets_a_damaged_file_aside(self):
        self.path.write_text('{"gemini_api_key": "abc", "trunc', encoding="utf-8")

        self.assertEqual(safe_io.read_json_for_update(self.path), {})

        kept = [p for p in self.dir.iterdir() if ".corrupt-" in p.name]
        self.assertEqual(len(kept), 1)
        self.assertIn("gemini_api_key", kept[0].read_text(encoding="utf-8"))
        # The original stays where it was until something is written over it.
        self.assertTrue(self.path.exists())

    def test_read_for_update_sets_aside_a_file_that_is_not_an_object(self):
        self.path.write_text('["a", "list"]', encoding="utf-8")

        self.assertEqual(safe_io.read_json_for_update(self.path), {})
        self.assertEqual(
            len([p for p in self.dir.iterdir() if ".corrupt-" in p.name]), 1)

    def test_two_quarantines_in_the_same_second_do_not_collide(self):
        self.path.write_text("not json", encoding="utf-8")
        with patch.object(safe_io.time, "strftime", return_value="20260101-000000"):
            first = safe_io.quarantine(self.path)
            second = safe_io.quarantine(self.path)

        self.assertNotEqual(first, second)
        self.assertTrue(first.exists() and second.exists())


if __name__ == "__main__":
    unittest.main()
