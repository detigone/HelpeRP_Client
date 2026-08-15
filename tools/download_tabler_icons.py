#!/usr/bin/env python3
"""Скачивание иконок из Tabler Icons (https://github.com/tabler/tabler-icons).

Скачивает SVG-иконки и конвертирует их в настоящие PNG-файлы.
"""
from __future__ import annotations

import os
import shutil
import sys
import urllib.request
from pathlib import Path

# Консоль Windows может не поддерживать UTF-8-символы в cp1251.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = ROOT / "assets" / "icons"

# Таблица маппинга: локальное имя -> иконка из Tabler
TABLER_ICONS_MAP = {
    # Фракции
    "logo": "brand-github",  # Используем GitHub как логотип
    "rules": "book-2",
    "moderator": "shield-check",
    "admin": "crown",
    "editor": "search",
    "management": "briefcase",
    "star": "star",
    "owner": "lock",
    "fire": "flame",
    "support": "headphones",
    "web": "world",
    "developer": "code",
    "punishment": "gavel",

    # Компоненты интерфейса
    "home": "home",
    "copy": "copy",
    "ai": "brain",
    "frequent": "bolt",
    "settings": "settings",
    "warning": "alert-triangle",
    "like": "heart",
    "expand": "chevron-down",
    "collapse": "chevron-up",
    "bolt": "zap",
    "bot": "robot",
    "verified": "check",
    "info": "info-circle",
    "logs": "list",
    "video": "video",
    "calendar": "calendar",
    "new": "star",
}

# Скачиваем SVG из CDN Tabler (outline)
TABLER_BASE_URL = "https://cdn.jsdelivr.net/gh/tabler/tabler-icons@latest/icons/outline"


def download_icon(name: str, tabler_name: str) -> bool:
    """Скачать SVG-иконку из Tabler Icons CDN и сконвертировать в настоящий PNG.

    Ошибка прошлых версий: URL имел расширение .svg, но сохранялся в файл .png
    без конвертации — в assets/icons лежали SVG-файлы под видом PNG, из-за чего
    Pillow не мог их открыть и иконки не отображались.
    """
    icon_url = f"{TABLER_BASE_URL}/{tabler_name}.svg"
    svg_path = ICONS_DIR / f"{name}.svg"
    png_path = ICONS_DIR / f"{name}.png"

    try:
        print(f"  {name:20s} <- {tabler_name:20s} ", end="", flush=True)
        urllib.request.urlretrieve(icon_url, str(svg_path))
        if not _convert_svg_to_png(svg_path, png_path):
            raise RuntimeError("не удалось сконвертировать SVG -> PNG")
        svg_path.unlink(missing_ok=True)  # Удалим временный SVG
        print("OK")
        return True
    except Exception as e:
        svg_path.unlink(missing_ok=True)
        print(f"FAIL ({e})")
        return False


def _convert_svg_to_png(svg_path: Path, png_path: Path, size: int = 24) -> bool:
    """Сконвертировать SVG в настоящий PNG через cairosvg."""
    try:
        import cairosvg
        cairosvg.svg2png(
            bytestring=svg_path.read_bytes(),
            write_to=str(png_path),
            output_width=size,
            output_height=size,
        )
        return True
    except ImportError:
        return False
    except Exception:
        return False


def main():
    print("=" * 60)
    print("Tabler Icons Downloader для HelpeRP")
    print("=" * 60)
    print()

    # Очистить старые иконки (кроме logo.ico и logo.png)
    if ICONS_DIR.exists():
        print(f"[1/3] Очистка иконок в {ICONS_DIR}...")
        for icon_file in ICONS_DIR.glob("*"):
            if icon_file.name not in ("logo.png", "logo.ico"):
                try:
                    if icon_file.is_file():
                        icon_file.unlink()
                except Exception:
                    pass
        print("OK. Старые иконки удалены\n")

    ICONS_DIR.mkdir(parents=True, exist_ok=True)

    # Скачать и сконвертировать новые иконки
    print("[2/3] Скачивание иконок из Tabler Icons (SVG -> PNG)...")
    print(f"      Источник: {TABLER_BASE_URL}\n")

    downloaded = 0
    failed = 0

    for local_name, tabler_name in sorted(TABLER_ICONS_MAP.items()):
        if download_icon(local_name, tabler_name):
            downloaded += 1
        else:
            failed += 1

    print(f"\nOK. Скачано и сконвертировано: {downloaded}")
    if failed > 0:
        print(f"FAIL. Ошибок: {failed}")
    print()

    # Сводка
    print("[Завершение]")
    png_count = len(list(ICONS_DIR.glob("*.png")))
    svg_count = len(list(ICONS_DIR.glob("*.svg")))
    print(f"Иконки загружены в: {ICONS_DIR}")
    print(f"PNG файлов: {png_count}")
    if svg_count > 0:
        print(f"SVG файлов (не сконвертированы): {svg_count}")
    print()

    if png_count > 25:
        print("OK. Иконки успешно обновлены!")
    else:
        print("WARN. Не удалось скачать достаточно иконок")
    print()
    print("Рекомендация: Перезагрузите приложение для применения новых иконок")


if __name__ == "__main__":
    main()
