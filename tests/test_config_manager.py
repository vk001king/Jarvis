import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from memory import config_manager


class ConfigManagerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name) / "config"
        self.file = self.dir / "api_keys.json"
        for name, value in (("CONFIG_DIR", self.dir), ("CONFIG_FILE", self.file)):
            patcher = patch.object(config_manager, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _stored(self) -> dict:
        return json.loads(self.file.read_text(encoding="utf-8"))

    def test_setters_only_touch_their_own_keys(self):
        config_manager.save_api_keys("  key-0123456789abcdef  ")
        config_manager.save_assistant_config("Friday", " Sam ")
        config_manager.save_voice("Kore")
        config_manager.save_wake_word_enabled(True)
        config_manager.save_hud_style("face")
        config_manager.save_plugin_enabled("github", False)
        config_manager.save_plugin_config("github", {"token": "t1"})
        config_manager.save_plugin_config("github", {"user": "sam"})
        config_manager.save_turn_tuning({"enabled": True})
        config_manager.save_turn_tuning({"silence_ms": 700})

        self.assertEqual(self._stored(), {
            "gemini_api_key": "key-0123456789abcdef",
            "assistant_name": "Friday",
            "user_name": "Sam",
            "voice_name": "Kore",
            "wake_word_enabled": True,
            "hud_style": "face",
            "plugins_enabled": {"github": False},
            "plugin_config": {"github": {"token": "t1", "user": "sam"}},
            "turn_tuning": {"enabled": True, "silence_ms": 700},
        })
        self.assertTrue(config_manager.is_configured())
        self.assertFalse(config_manager.get_plugin_enabled("github"))
        self.assertTrue(config_manager.get_plugin_enabled("never_seen"))
        self.assertEqual(config_manager.get_plugin_setting("github", "token"), "t1")

    def test_invalid_values_fall_back_to_safe_defaults(self):
        config_manager.save_voice("NotAVoice")
        config_manager.save_hud_style("hologram")
        config_manager.save_media_resolution("ultra")

        self.assertEqual(config_manager.get_voice(), config_manager.DEFAULT_VOICE)
        self.assertEqual(config_manager.get_hud_style(), "core")
        self.assertEqual(config_manager.get_media_resolution(), "medium")

    def test_a_damaged_config_is_kept_aside_instead_of_being_wiped(self):
        self.dir.mkdir(parents=True)
        self.file.write_text('{"gemini_api_key": "precious-key", "plugin_co',
                             encoding="utf-8")

        config_manager.save_wake_word_enabled(True)

        self.assertEqual(self._stored(), {"wake_word_enabled": True})
        kept = [p for p in self.dir.iterdir() if ".corrupt-" in p.name]
        self.assertEqual(len(kept), 1)
        self.assertIn("precious-key", kept[0].read_text(encoding="utf-8"))

    def test_getters_survive_a_config_that_is_not_an_object(self):
        self.dir.mkdir(parents=True)
        self.file.write_text("[1, 2, 3]", encoding="utf-8")

        self.assertEqual(config_manager.load_api_keys(), {})
        self.assertEqual(config_manager.get_assistant_name(), "JARVIS")
        self.assertFalse(config_manager.is_configured())

    def test_malformed_plugin_flags_do_not_disable_or_crash_plugins(self):
        self.dir.mkdir(parents=True)
        self.file.write_text('{"plugins_enabled": "yes"}', encoding="utf-8")

        self.assertTrue(config_manager.get_plugin_enabled("github"))
        config_manager.save_plugin_enabled("github", False)
        self.assertEqual(self._stored()["plugins_enabled"], {"github": False})

    def test_concurrent_setters_do_not_lose_each_others_writes(self):
        def worker(index: int) -> None:
            config_manager.save_plugin_config(f"plugin_{index}", {"n": index})
            config_manager.update_config(**{f"flag_{index}": index})

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(24)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        stored = self._stored()
        self.assertEqual(len(stored["plugin_config"]), 24)
        self.assertEqual(sum(1 for key in stored if key.startswith("flag_")), 24)


if __name__ == "__main__":
    unittest.main()
