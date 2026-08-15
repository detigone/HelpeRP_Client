"""Загрузка PNG-иконок для интерфейса HelpeRP.

Оптимизация: вместо попиксельной маски (удаление чёрного фона) на каждый вызов
теперь используются настоящие RGBA-иконки. Кэшируется уже обработанное
изображение, повторное масштабирование выполняется быстро через Pillow.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from core.paths import icons_dir

ICONS_DIR = Path(icons_dir())

# id фракции → файл иконки (из Tabler Icons)
FACTION_ICONS = {
    "all": "logo.png",
    "legislation": "rules.png",
    "mvd": "moderator.png",
    "fsb": "admin.png",
    "sk": "editor.png",
    "prokuratura": "management.png",
    "rosgvardia": "star.png",
    "fsin": "owner.png",
    "mchs": "fire.png",
    "smp": "support.png",
    "smi": "web.png",
    "army": "developer.png",
    "crime": "punishment.png",
    "terminology": "logo.png",
}

# Иконки интерфейса (из Tabler Icons)
UI_ICONS = {
    "app": "logo.png",
    "home": "home.png",
    "copy": "copy.png",
    "ai": "ai.png",
    "frequent": "frequent.png",
    "star": "star.png",
    "settings": "settings.png",
    "rules": "rules.png",
    "search": "bolt.png",
    "warning": "warning.png",
    "like": "like.png",
    "expand": "expand.png",
    "collapse": "collapse.png",
}

# Высокое разрешение для ретинки (PNG → апскейл-кратность)
_RETINA = 3

_cache: dict[tuple[str, int], ctk.CTkImage] = {}


@lru_cache(maxsize=128)
def _load_rgba(name: str) -> Image.Image | None:
    """Прочитать настоящий PNG и вернуть его в режиме RGBA (с кэшем)."""
    path = ICONS_DIR / name
    if not path.is_file():
        return None
    try:
        return Image.open(path).convert("RGBA")
    except OSError:
        return None


def _scaled(name: str, size: int) -> Image.Image | None:
    """Подготовить RGBA-изображение нужного размера (для ретинки)."""
    img = _load_rgba(name)
    if img is None:
        return None
    # Кэшируем крупный вариант, чтобы получить резкие иконки на ретинке.
    return img.resize((size * _RETINA, size * _RETINA), Image.LANCZOS)


def get_icon(name: str, size: int = 22) -> ctk.CTkImage | None:
    """Вернуть CTkImage для иконки (с кэшем готовых изображений)."""
    key = (name, size)
    if key in _cache:
        return _cache[key]

    pil = _scaled(name, size)
    if pil is None:
        return None

    img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(size, size))
    _cache[key] = img
    return img


def ui_icon(key: str, size: int = 22) -> ctk.CTkImage | None:
    filename = UI_ICONS.get(key)
    return get_icon(filename, size) if filename else None


def faction_icon(faction_id: str, size: int = 22) -> ctk.CTkImage | None:
    filename = FACTION_ICONS.get(faction_id)
    return get_icon(filename, size) if filename else None


# Эмодзи-иконки для навигации и элементов (всегда отображаются на Windows).
NAV_EMOJI = {
    "database": "📚",
    "measures": "⚖",
    "templates": "📋",
    "settings": "⚙",
}


def nav_emoji(key: str) -> str:
    """Вернуть эмодзи для пункта навигации (или пустую строку)."""
    return NAV_EMOJI.get(key, "")


def faction_emoji(faction_id: str) -> str:
    """Вернуть эмодзи для фракции (из реестра factions.py, поле icon)."""
    try:
        from core.factions import get_faction_by_id
        fac = get_faction_by_id(faction_id)
        return fac.get("icon", "")
    except Exception:
        return ""


def preload():
    """Предзагрузка часто используемых иконок."""
    for name in set(FACTION_ICONS.values()) | set(UI_ICONS.values()):
        get_icon(name, 16)
        get_icon(name, 20)
        get_icon(name, 22)
        get_icon(name, 28)
