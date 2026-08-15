"""Глобальные хоткеи с перепривязкой.

Внимание: keyboard.remove_hotkey() принимает ХЭНДЛ (число), возвращаемый
keyboard.add_hotkey(), а не строку горячей клавиши. Прошлая версия хранила
строку и вызывала remove_hotkey(строка) — биндинги не снимались и накапливались
(утечка) при каждой перепривязке из настроек.
"""

from __future__ import annotations

import keyboard

# name -> (hotkey_строка, callback, handle)
_bindings: dict[str, dict] = {}


def bind(name: str, hotkey: str, callback) -> None:
    """Зарегистрировать или обновить хоткей по имени."""
    unbind(name)
    try:
        handle = keyboard.add_hotkey(hotkey, callback, suppress=False)
        _bindings[name] = {"hotkey": hotkey, "callback": callback, "handle": handle}
    except Exception as e:
        print(f"[Hotkeys] Не удалось привязать {hotkey} ({name}): {e}")


def unbind(name: str) -> None:
    entry = _bindings.pop(name, None)
    if not entry:
        return
    try:
        keyboard.remove_hotkey(entry["handle"])
    except Exception:
        pass


def rebind_all_from_config(app_window) -> None:
    """Перечитать хоткеи из settings.json и привязать к окну."""
    from core.config import app_config

    hk = app_config.get("hotkeys", {})
    toggle = hk.get("toggle_overlay", "shift+\\")
    hide = hk.get("hide_window", "ctrl+shift+h")
    favorites = hk.get("favorites_overlay", app_config.get("favorites", {}).get("hotkey", "ctrl+alt+f"))

    bind("toggle_mode", toggle, app_window.toggle_visibility)
    bind("hide_window", hide, app_window.toggle_hidden)
    bind("favorites_overlay", favorites, app_window.toggle_favorites_overlay)
