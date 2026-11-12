import json
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from actions import background_monitor
from memory import memory_manager

GITHUB_TOKEN = "ghp_" + "A1b2" * 9


class MemoryManagerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name) / "memory"
        self.file = self.dir / "long_term.json"
        patcher = patch.object(memory_manager, "MEMORY_PATH", self.file)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _stored(self) -> dict:
        return json.loads(self.file.read_text(encoding="utf-8"))

    def test_remember_recall_and_forget(self):
        self.assertEqual(memory_manager.remember("sister_name", "Ayşe", "relationships"),
                         "Remembered: relationships/sister_name = Ayşe")

        self.assertIn("relationships/sister name: Ayşe",
                      memory_manager.search_memory("sister"))
        self.assertIn("Ayşe", self.file.read_text(encoding="utf-8"))
        self.assertEqual(memory_manager.forget("sister_name", "relationships"),
                         "Forgotten: relationships/sister_name")
        self.assertEqual(memory_manager.forget("sister_name", "relationships"),
                         "Not found: relationships/sister_name")
        self.assertEqual(memory_manager.search_memory("sister"),
                         "Nothing stored about 'sister'.")

    def test_unknown_categories_are_filed_under_notes(self):
        memory_manager.remember("github_status", "account connected", "credentials")

        stored = self._stored()
        self.assertNotIn("credentials", stored)
        self.assertEqual(stored["notes"]["github_status"]["value"], "account connected")

    def test_a_fact_cannot_overwrite_the_bookkeeping_sections(self):
        memory_manager.save_session_summary("Talked about the school project.")
        background_monitor.add_monitor("space exploration")

        memory_manager.update_memory({
            "sessions": {"oops": {"value": "x"}},
            "monitors": {"oops": {"value": "y"}},
        })

        stored = self._stored()
        self.assertEqual([s["summary"] for s in stored["sessions"]],
                         ["Talked about the school project."])
        self.assertEqual(list(stored["monitors"]), ["space_exploration"])
        self.assertEqual(background_monitor.list_monitors(), ["space exploration"])
        self.assertEqual(stored["notes"]["oops"]["value"], "y")

    def test_credentials_are_refused_and_never_reach_the_file(self):
        result = memory_manager.remember("github_token", GITHUB_TOKEN, "notes")

        self.assertTrue(result.startswith("[NOT_SAVED]"))
        self.assertIn("GitHub token", result)
        self.assertNotIn(GITHUB_TOKEN, result)
        self.assertFalse(self.file.exists())

        memory_manager.update_memory({"notes": {
            "work_token": {"value": f"use {GITHUB_TOKEN} for work"},
            "favorite_food": {"value": "pizza"},
        }})
        text = self.file.read_text(encoding="utf-8")
        self.assertNotIn(GITHUB_TOKEN, text)
        self.assertIn("pizza", text)

    def test_a_personal_password_the_user_asked_to_keep_is_still_stored(self):
        result = memory_manager.remember("guest_wifi_password", "hunter2-guest", "notes")

        self.assertTrue(result.startswith("Remembered"))
        self.assertIn("hunter2-guest", memory_manager.search_memory("wifi"))

    def test_recall_masks_a_credential_stored_before_the_guard_existed(self):
        self.dir.mkdir(parents=True)
        self.file.write_text(json.dumps({
            "credentials": {"github_token": {"value": GITHUB_TOKEN, "updated": "2026-11-09"}},
        }), encoding="utf-8")

        recalled = memory_manager.search_memory("github")

        self.assertIn("github token", recalled)
        self.assertNotIn(GITHUB_TOKEN, recalled)
        self.assertIn("[hidden]", recalled)
        # The memory panel still shows it, so the user can find and delete it.
        self.assertEqual(memory_manager.all_entries_for_ui()[0]["value"], GITHUB_TOKEN)
        self.assertEqual(memory_manager.forget("github_token", "credentials"),
                         "Forgotten: credentials/github_token")

    def test_a_damaged_memory_file_is_kept_aside_before_the_next_save(self):
        self.dir.mkdir(parents=True)
        self.file.write_text('{"relationships": {"sister_name": {"value": "Ayşe"', encoding="utf-8")

        self.assertEqual(memory_manager.load_memory()["relationships"], {})
        memory_manager.remember("favorite_food", "pizza", "preferences")

        kept = [p for p in self.dir.iterdir() if ".corrupt-" in p.name]
        self.assertEqual(len(kept), 1)
        self.assertIn("Ayşe", kept[0].read_text(encoding="utf-8"))
        self.assertEqual(self._stored()["preferences"]["favorite_food"]["value"], "pizza")

    def test_forget_ignores_sections_that_are_not_fact_tables(self):
        memory_manager.save_session_summary("A summary.")

        self.assertEqual(memory_manager.forget("0", "sessions"), "Not found: sessions/0")
        self.assertEqual(len(self._stored()["sessions"]), 1)

    def test_session_summaries_are_consumed_once_and_masked(self):
        memory_manager.save_session_summary(f"Set up GitHub with {GITHUB_TOKEN}.", "en")

        entry = memory_manager.pop_last_session()

        self.assertEqual(entry["language"], "en")
        self.assertNotIn(GITHUB_TOKEN, entry["summary"])
        self.assertIsNone(memory_manager.pop_last_session())

    def test_concurrent_writers_do_not_erase_each_other(self):
        def facts(index: int) -> None:
            memory_manager.remember(f"fact_{index}", f"value {index}", "notes")

        def monitors(index: int) -> None:
            background_monitor.add_monitor(f"topic number {index}")

        threads = [threading.Thread(target=fn, args=(i,))
                   for i in range(12) for fn in (facts, monitors)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        stored = self._stored()
        self.assertEqual(len(stored["notes"]), 12)
        self.assertEqual(len(stored["monitors"]), 12)

    def test_monitor_topics_in_any_script_get_their_own_entry(self):
        self.assertEqual(background_monitor.add_monitor("宇宙探査"), "Now monitoring: 宇宙探査")
        self.assertEqual(background_monitor.add_monitor("人工知能"), "Now monitoring: 人工知能")
        self.assertEqual(background_monitor.add_monitor("宇宙探査"), "Already monitoring: 宇宙探査")

        self.assertEqual(sorted(background_monitor.list_monitors()), ["人工知能", "宇宙探査"])
        self.assertEqual(background_monitor.remove_monitor("人工知能"),
                         "Stopped monitoring: 人工知能")
        self.assertEqual(background_monitor.list_monitors(), ["宇宙探査"])
        self.assertEqual(background_monitor.add_monitor("bitcoin price"),
                         "I don't monitor crypto or financial topics.")

    def test_daily_check_keeps_changes_made_while_it_was_searching(self):
        background_monitor.add_monitor("space exploration")
        background_monitor.add_monitor("old topic")

        def fake_news(topic, max_results=5):
            # The user speaks while the search is on the network.
            background_monitor.add_monitor("added meanwhile")
            background_monitor.remove_monitor("old topic")
            memory_manager.remember("favorite_food", "pizza", "preferences")
            return [{"title": f"Headline about {topic}", "snippet": "s", "source": "src"}]

        fake_module = types.ModuleType("actions.web_search")
        fake_module._ddg_news = fake_news
        with patch.dict(sys.modules, {"actions.web_search": fake_module}):
            alerts = background_monitor.check_all()
            repeat = background_monitor.check_all()

        self.assertEqual(len(alerts), 2)
        self.assertTrue(alerts[0].startswith("[MONITOR_ALERT] space exploration"))
        stored = self._stored()
        self.assertEqual(sorted(stored["monitors"]),
                         ["added_meanwhile", "space_exploration"])
        self.assertTrue(stored["monitors"]["space_exploration"]["last_hash"])
        self.assertEqual(stored["preferences"]["favorite_food"]["value"], "pizza")
        # The topic added mid-run is checked on the next pass; the rest are done.
        self.assertEqual(len(repeat), 1)
        self.assertTrue(repeat[0].startswith("[MONITOR_ALERT] added meanwhile"))

    def test_prompt_block_lists_identity_and_indexes_the_overflow(self):
        memory_manager.remember("name", "Sam", "identity")
        for index in range(30):
            memory_manager.remember(f"hobby_{index}", "x" * 60, "preferences")

        block = memory_manager.format_memory_for_prompt(memory_manager.load_memory())

        self.assertIn("Name: Sam", block)
        self.assertIn("[ALSO REMEMBERED", block)
        self.assertLess(len(block), 2200)


if __name__ == "__main__":
    unittest.main()
