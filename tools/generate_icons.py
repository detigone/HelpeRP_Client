#!/usr/bin/env python3
"""Генерация PNG-иконок HelpeRP через Pillow (без native-зависимостей).

Выбранный подход (Вариант B): иконки рисуются программно через Pillow —
монохромные глифы в акцентных цветах фракций на прозрачном фоне. Это надёжно,
не требует cairo/svglib и позволяет перекрашивать иконки под каждую фракцию.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = ROOT / "assets" / "icons"

# Размер исходной иконки (увеличиваем для ретинки).
SIZE = 64

# Таблица: имя иконки -> (глиф, акцентный цвет).
# Цвета согласованы с акцентами фракций в core/factions.py.
ICONS = {
    # Логотип и "Все базы"
    "logo": ("H", "#7c3aed"),
    # Фракции
    "rules": ("⚖", "#4a9eff"),
    "moderator": ("М", "#2563eb"),
    "admin": ("Ф", "#b91c1c"),
    "editor": ("С", "#7c3aed"),
    "management": ("П", "#1e3a5f"),
    "star": ("Р", "#ca8a04"),
    "owner": ("И", "#52525b"),
    "fire": ("МЧ", "#ea580c"),
    "support": ("СМ", "#059669"),
    "web": ("СМ", "#d97706"),
    "developer": ("А", "#4d7c0f"),
    "punishment": ("К", "#9333ea"),
    # Интерфейс
    "home": ("⌂", "#a1a8b5"),
    "copy": ("⧉", "#a1a8b5"),
    "ai": ("AI", "#7c3aed"),
    "frequent": ("★", "#f59e0b"),
    "settings": ("⚙", "#a1a8b5"),
    "warning": ("!", "#ef4444"),
    "like": ("♥", "#ef4444"),
    "expand": ("▾", "#a1a8b5"),
    "collapse": ("▴", "#a1a8b5"),
    "bolt": ("⚡", "#f59e0b"),
    "bot": ("B", "#a1a8b5"),
    "verified": ("✓", "#22c55e"),
    "info": ("i", "#8b5cf6"),
    "logs": ("≡", "#a1a8b5"),
    "video": ("▶", "#a1a8b5"),
    "calendar": ("▦", "#a1a8b5"),
    "new": ("+", "#22c55e"),
}


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Подобрать шрифт с поддержкой глифа."""
    candidates = [
        "C:/Windows/Fonts/segoeuiemj.ttf",
        "C:/Windows/Fonts/seguisym.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def generate_icon(name: str, glyph: str, color: str) -> bool:
    """Нарисовать PNG-иконку: глиф в цвете на прозрачном фоне."""
    try:
        img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        font = _font(int(SIZE * 0.62))
        bbox = draw.textbbox((0, 0), glyph, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (SIZE - tw) / 2 - bbox[0]
        y = (SIZE - th) / 2 - bbox[1]

        draw.text((x, y), glyph, font=font, fill=color)
        img.save(ICONS_DIR / f"{name}.png")
        return True
    except Exception as e:
        print(f"  {name:20s} FAIL ({e})")
        return False


def main():
    print("=" * 60)
    print("Генератор PNG-иконок HelpeRP (Pillow, без cairo)")
    print("=" * 60)
    ICONS_DIR.mkdir(parents=True, exist_ok=True)

    ok, fail = 0, 0
    for name, (glyph, color) in ICONS.items():
        if generate_icon(name, glyph, color):
            ok += 1
        else:
            fail += 1

    # Дополнительно сгенерировать logo.ico (используется как иконка exe).
    try:
        logo = Image.open(ICONS_DIR / "logo.png").convert("RGBA")
        logo.save(ICONS_DIR / "logo.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
        print("  logo.ico            OK")
    except Exception as e:
        print(f"  logo.ico            FAIL ({e})")

    print(f"\nOK. Сгенерировано: {ok}")
    if fail:
        print(f"FAIL. Ошибок: {fail}")
    print("Готово.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()