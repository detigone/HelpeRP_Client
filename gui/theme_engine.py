"""Применение темы оформления к gui.theme и окну."""

from __future__ import annotations

from gui import theme as T
from gui.palettes import PRESETS, resolve_palette


def _apply_to_module(palette: dict) -> None:
    mapping = {
        "bg_root": "BG_ROOT",
        "bg_sidebar": "BG_SIDEBAR",
        "bg_panel": "BG_PANEL",
        "bg_card": "BG_CARD",
        "bg_input": "BG_INPUT",
        "bg_hover": "BG_HOVER",
        "bg_selected": "BG_SELECTED",
        "border": "BORDER",
        "border_light": "BORDER_LIGHT",
        "text_primary": "TEXT_PRIMARY",
        "text_secondary": "TEXT_SECONDARY",
        "text_muted": "TEXT_MUTED",
        "accent": "DEFAULT_ACCENT",
        "accent_hover": "DEFAULT_ACCENT_HOVER",
    }
    for src, dst in mapping.items():
        if src in palette:
            setattr(T, dst, palette[src])


def load_theme_from_config() -> dict:
    from core.config import app_config

    ui = app_config.get("ui", {}) or {}
    preset = ui.get("theme", "helperp")
    custom = ui.get("custom_accent", "")
    palette = resolve_palette(preset, custom)
    _apply_to_module(palette)
    return palette


def get_theme_accent() -> str:
    return T.DEFAULT_ACCENT


def get_theme_accent_hover() -> str:
    return T.DEFAULT_ACCENT_HOVER


def effective_accent(faction_accent: str) -> tuple[str, str]:
    """Акцент UI: фракция или тема."""
    from core.config import app_config

    if app_config.get("ui", {}).get("use_faction_accent", True):
        from core.factions import get_faction
        fac = get_faction(app_config.get("current_faction", "Все базы"))
        return fac["accent"], fac.get("accent_hover", T.DEFAULT_ACCENT_HOVER)
    return T.DEFAULT_ACCENT, T.DEFAULT_ACCENT_HOVER
