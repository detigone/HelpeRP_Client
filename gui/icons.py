"""Загрузка PNG-иконок для интерфейса HelpeRP."""

from pathlib import Path

import customtkinter as ctk
from PIL import Image

from core.paths import icons_dir

ICONS_DIR = Path(icons_dir())

# id фракции → файл иконки
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

UI_ICONS = {
    "app": "logo.png",
    "home": "home.png",
    "copy": "logs.png",
    "ai": "bot.png",
    "frequent": "verified.png",
    "star": "star.png",
    "settings": "info.png",
    "rules": "rules.png",
    "search": "bolt.png",
    "warning": "warning.png",
    "like": "like.png",
    "expand": "bolt.png",
    "collapse": "warning.png",
}

_cache: dict[tuple[str, int], ctk.CTkImage] = {}


def _prepare_rgba(path: Path) -> Image.Image:
    """Чёрный фон PNG → прозрачность для тёмной темы."""
    img = Image.open(path).convert("RGBA")
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r < 28 and g < 28 and b < 28:
                pixels[x, y] = (0, 0, 0, 0)
    return img


def get_icon(name: str, size: int = 22) -> ctk.CTkImage | None:
    key = (name, size)
    if key in _cache:
        return _cache[key]

    path = ICONS_DIR / name
    if not path.is_file():
        return None

    try:
        pil = _prepare_rgba(path)
        img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(size, size))
        _cache[key] = img
        return img
    except OSError:
        return None


def ui_icon(key: str, size: int = 22) -> ctk.CTkImage | None:
    filename = UI_ICONS.get(key)
    return get_icon(filename, size) if filename else None


def faction_icon(faction_id: str, size: int = 22) -> ctk.CTkImage | None:
    filename = FACTION_ICONS.get(faction_id)
    return get_icon(filename, size) if filename else None


def preload():
    """Предзагрузка часто используемых иконок."""
    for name in set(FACTION_ICONS.values()) | set(UI_ICONS.values()):
        get_icon(name, 20)
        get_icon(name, 22)
        get_icon(name, 28)
