"""Пути приложения — dev и PyInstaller (.exe)."""

from __future__ import annotations

import os
import sys


def is_frozen() -> bool:
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def app_dir() -> str:
    """Папка exe / проекта — здесь settings.json."""
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def bundle_dir() -> str:
    """Ресурсы (data, assets, legal) — в exe лежат в _MEIPASS."""
    if is_frozen():
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def data_dir() -> str:
    return os.path.join(bundle_dir(), "data")


def assets_dir() -> str:
    return os.path.join(bundle_dir(), "assets")


def icons_dir() -> str:
    return os.path.join(assets_dir(), "icons")


def legal_dir() -> str:
    return os.path.join(bundle_dir(), "legal")


def docs_dir() -> str:
    return os.path.join(bundle_dir(), "docs")


def updates_dir() -> str:
    return os.path.join(bundle_dir(), "updates")


def settings_path() -> str:
    return os.path.join(app_dir(), "settings.json")
