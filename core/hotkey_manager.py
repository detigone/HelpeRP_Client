"""Глобальные хоткеи с перепривязкой."""

import keyboard

_bindings: dict[str, tuple[str, callable]] = {}


def bind(name: str, hotkey: str, callback):
    """Зарегистрировать или обновить хоткей по имени."""
    unbind(name)
    try:
        keyboard.add_hotkey(hotkey, callback, suppress=False)
        _bindings[name] = (hotkey, callback)
    except Exception as e:
        print(f"[Hotkeys] Не удалось привязать {hotkey} ({name}): {e}")


def unbind(name: str):
    entry = _bindings.pop(name, None)
    if not entry:
        return
    hotkey, _ = entry
    try:
        keyboard.remove_hotkey(hotkey)
    except Exception:
        pass


def rebind_all_from_config(app_window):
    """Перечитать хоткеи из settings.json и привязать к окну."""
    from core.config import app_config

    hk = app_config.get("hotkeys", {})
    toggle = hk.get("toggle_overlay", "shift+\\")
    hide = hk.get("hide_window", "ctrl+shift+h")

    bind("toggle_mode", toggle, app_window.toggle_visibility)
    bind("hide_window", hide, app_window.toggle_hidden)
