# HelpeRP_Client/core/config.py
import copy
import json
import os

from core.paths import settings_path

_BAD_BASE_URLS = {
    "https://openai.com",
    "http://openai.com",
    "https://www.openai.com",
    "openai.com",
}


def _deep_merge(base: dict, overlay: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def normalize_base_url(url: str) -> str:
    url = (url or "").strip().rstrip("/")
    if not url:
        return "https://api.openai.com/v1"
    if url.lower() in _BAD_BASE_URLS or url.lower().replace("https://", "").replace("http://", "") == "openai.com":
        return "https://api.openai.com/v1"
    if not url.startswith("http"):
        url = "https://" + url
    if "openai" in url.lower() and not url.endswith("/v1"):
        url = url.rstrip("/") + "/v1"
    return url


def is_local_ai_endpoint(base_url: str, provider: str = "") -> bool:
    from core.local_ai import is_local_provider

    if is_local_provider(provider):
        return True
    url = (base_url or "").lower()
    return "localhost" in url or "127.0.0.1" in url


def effective_api_key(api_key: str, base_url: str = "", provider: str = "") -> str:
    if not is_placeholder_api_key(api_key):
        return api_key.strip()
    if is_local_ai_endpoint(base_url, provider):
        return "ollama"
    return ""


def is_placeholder_api_key(key: str) -> bool:
    k = (key or "").strip().upper()
    return not k or k in ("YOUR_AI_API_KEY", "SK-...", "API_KEY", "CHANGE_ME")


class Config:
    def __init__(self, config_path: str | None = None):
        self.config_filename = config_path or settings_path()
        self.default_settings = {
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
            "ai_provider": "openai",
            "current_faction": "Все базы",
            "character": {
                "name": "Иван Иванов",
                "rank": "Рядовой",
                "badge": "№0000",
                "personality": "Вежливый, строго следует уставу, говорит уверенно",
            },
            "characters": [],
            "active_character_id": "",
            "game": {"chat_key": "t"},
            "ui": {
                "list_limit": 120,
                "auto_send_ai": False,
                "animations": False,
                "theme": "helperp",
                "use_faction_accent": True,
                "custom_accent": "",
            },
            "recent": [],
            "favorites": {
                "items": [],
                "hotkey": "ctrl+alt+f",
                "mode": "compact",
                "max_items": 8,
            },
            "discord": {
                "enabled": False,
                "client_id": "",
                "details": "HelpeRP — база знаний",
                "state": "Режим поиска и подготовки RP",
                "button_label": "Открыть HelpeRP",
                "button_url": "https://yeolka-lm.github.io/HelpeRP_Client/",
            },
            "hotkeys": {
                "toggle_overlay": "shift+\\",
                "hide_window": "ctrl+shift+h",
                "submit_request": "enter",
                "favorites_overlay": "ctrl+alt+f",
            },
            "license": {"eula_accepted": False, "eula_version": "1.1"},
            "updates": {
                "auto_check": True,
                "auto_download": True,
                "check_interval_hours": 24,
                "last_check": None,
                "dismissed_version": "",
                "manifest_url": "",
            },
            "search": {
                "wikipedia": True,
                "online_fallback": True,
                "rag": True,
            },
        }
        self.settings = {}
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_filename):
            try:
                with open(self.config_filename, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self.settings = _deep_merge(self.default_settings, loaded)
                self._sanitize()
                self.save_config()
            except Exception as e:
                print(f"[Config] Ошибка чтения {self.config_filename}: {e}. Сброс.")
                self.settings = copy.deepcopy(self.default_settings)
                self.save_config()
        else:
            self.settings = copy.deepcopy(self.default_settings)
            self.save_config()

    def _sanitize(self):
        from core.secrets import protect_secret, unprotect_secret

        self.settings["base_url"] = normalize_base_url(self.settings.get("base_url", ""))
        raw_key = unprotect_secret(self.settings.get("api_key", ""))
        if is_placeholder_api_key(raw_key):
            self.settings["api_key"] = ""
        else:
            self.settings["api_key"] = raw_key
        if not self.settings.get("ai_provider"):
            from core.ai_providers import detect_provider
            self.settings["ai_provider"] = detect_provider(self.settings.get("base_url", ""))
        lic = self.settings.get("license")
        if isinstance(lic, dict):
            from core.licensing import migrate_license_cfg
            migrated = migrate_license_cfg(lic)
            if migrated != lic:
                self.settings["license"] = migrated

        favorites = self.settings.get("favorites")
        if not isinstance(favorites, dict):
            favorites = {}
        items = favorites.get("items")
        if not isinstance(items, list):
            items = []
        try:
            max_items = max(1, int(favorites.get("max_items", 8) or 8))
        except (TypeError, ValueError):
            max_items = 8
        self.settings["favorites"] = {
            "items": [
                {
                    "key": item.get("key") or item.get("id") or item.get("title"),
                    "title": item.get("title") or "Избранная запись",
                    "faction": item.get("faction") or self.settings.get("current_faction", "Все базы"),
                }
                for item in items
                if isinstance(item, dict)
            ][:max_items],
            "hotkey": (favorites.get("hotkey") or "ctrl+alt+f").strip() or "ctrl+alt+f",
            "mode": favorites.get("mode") or "compact",
            "max_items": max_items,
        }
        hotkeys = self.settings.get("hotkeys", {})
        if not isinstance(hotkeys, dict):
            hotkeys = {}
        hotkeys.setdefault("favorites_overlay", self.settings["favorites"]["hotkey"])
        self.settings["hotkeys"] = hotkeys

        discord_cfg = self.settings.get("discord")
        if not isinstance(discord_cfg, dict):
            discord_cfg = {}
        self.settings["discord"] = {
            "enabled": bool(discord_cfg.get("enabled", False)),
            "client_id": str(discord_cfg.get("client_id", "")).strip(),
            "details": (discord_cfg.get("details") or "HelpeRP — база знаний").strip() or "HelpeRP — база знаний",
            "state": (discord_cfg.get("state") or "Режим поиска и подготовки RP").strip() or "Режим поиска и подготовки RP",
            "button_label": (discord_cfg.get("button_label") or "Открыть HelpeRP").strip() or "Открыть HelpeRP",
            "button_url": (discord_cfg.get("button_url") or "https://yeolka-lm.github.io/HelpeRP_Client/").strip() or "https://yeolka-lm.github.io/HelpeRP_Client/",
        }
        from core.characters import migrate_characters_settings
        migrate_characters_settings(self.settings)

    def save_config(self):
        try:
            from core.secrets import protect_secret

            folder = os.path.dirname(self.config_filename)
            if folder:
                os.makedirs(folder, exist_ok=True)
            to_save = copy.deepcopy(self.settings)
            key = to_save.get("api_key", "")
            if key and not is_placeholder_api_key(key):
                to_save["api_key"] = protect_secret(key)
            with open(self.config_filename, "w", encoding="utf-8") as f:
                json.dump(to_save, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[Config] Не удалось сохранить: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        if key == "base_url":
            value = normalize_base_url(str(value))
        self.settings[key] = value
        self.save_config()


app_config = Config()
