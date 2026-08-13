#!/usr/bin/env python3
"""Генерация logo.ico для HelpeRP.exe из assets/icons/logo.png."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "assets" / "icons" / "logo.png"
ICO = ROOT / "assets" / "icons" / "logo.ico"


def main() -> Path | None:
    if not LOGO.is_file():
        print(f"Нет файла: {LOGO}")
        return None
    from PIL import Image
    img = Image.open(LOGO).convert("RGBA")
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(ICO, format="ICO", sizes=sizes)
    print(f"OK: {ICO}")
    return ICO


if __name__ == "__main__":
    main()
