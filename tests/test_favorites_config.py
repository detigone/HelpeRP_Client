import os
import tempfile
import unittest

from core import discord_presence as rpc
from core.config import Config, app_config


class FavoritesConfigTests(unittest.TestCase):
    def test_default_and_persistent_favorites_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "settings.json")
            cfg = Config(path)

            self.assertIsInstance(cfg.get("favorites", {}), dict)
            self.assertIsInstance(cfg.get("favorites", {}).get("items", []), list)

            cfg.set(
                "favorites",
                {
                    "items": [{"key": "a1", "title": "Статья № 1", "faction": "Все базы"}],
                    "hotkey": "ctrl+alt+f",
                    "mode": "faction",
                    "max_items": 8,
                },
            )

            roundtrip = Config(path)
            stored = roundtrip.get("favorites", {})
            self.assertEqual(stored["hotkey"], "ctrl+alt+f")
            self.assertEqual(stored["items"][0]["title"], "Статья № 1")
            self.assertEqual(stored["mode"], "faction")

    def test_license_cfg_remains_persisted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "settings.json")
            cfg = Config(path)
            cfg.set("license", {"eula_accepted": True, "eula_version": "1.1"})

            roundtrip = Config(path)
            self.assertTrue(roundtrip.get("license", {}).get("eula_accepted"))

    def test_discord_presence_toggle_really_works(self):
        original_settings = app_config.settings.copy()
        original_pypresence = rpc.pypresence

        class FakePresence:
            def __init__(self, client_id):
                self.client_id = client_id
                self.connected = False
                self.updated = None

            def connect(self):
                self.connected = True

            def update(self, **kwargs):
                self.updated = kwargs

            def clear(self):
                self.connected = False

            def close(self):
                self.connected = False

        try:
            rpc.pypresence = type("P", (), {"Presence": FakePresence})
            app_config.settings["discord"] = {
                "enabled": True,
                "client_id": "1234567890",
                "details": "HelpeRP — база знаний",
                "state": "Режим поиска и подготовки RP",
                "button_label": "Открыть HelpeRP",
                "button_url": "https://example.com",
            }
            rpc._RPC = None

            rpc.refresh_discord_presence()
            self.assertIsNotNone(rpc._RPC)
            self.assertTrue(rpc._RPC.connected)

            app_config.settings["discord"]["enabled"] = False
            rpc.refresh_discord_presence()
            self.assertIsNone(rpc._RPC)
        finally:
            app_config.settings = original_settings
            rpc.pypresence = original_pypresence
            rpc._RPC = None


if __name__ == "__main__":
    unittest.main()
