#!/usr/bin/env python3
"""Сборка HelpeRP.exe и подготовка папки dist/HelpeRP_Release."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    print("=== HelpeRP — сборка exe ===\n")

    icon_script = ROOT / "tools" / "generate_icon.py"
    if icon_script.is_file():
        subprocess.check_call([sys.executable, str(icon_script)], cwd=str(ROOT))

    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("Устанавливаю PyInstaller…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    subprocess.check_call(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", str(ROOT / "HelpeRP.spec")],
        cwd=str(ROOT),
    )

    release = ROOT / "dist" / "HelpeRP_Release"
    release.mkdir(parents=True, exist_ok=True)

    exe_src = ROOT / "dist" / "HelpeRP.exe"
    if not exe_src.is_file():
        print("Ошибка: HelpeRP.exe не создан")
        sys.exit(1)

    shutil.copy2(exe_src, release / "HelpeRP.exe")

    for name in ("settings.json.example", "LICENSE", "THIRD_PARTY_NOTICES.md"):
        src = ROOT / name
        if src.is_file():
            shutil.copy2(src, release / name)

    keys_src = ROOT / "legal" / "LICENSE_KEYS_EXAMPLE.txt"
    if keys_src.is_file():
        shutil.copy2(keys_src, release / "LICENSE_KEYS_EXAMPLE.txt")

    print(f"\nГотово: {release}")
    print("  HelpeRP.exe")
    print("  settings.json.example")
    print("  LICENSE_KEYS_EXAMPLE.txt  (только для продавца — не отдавать покупателям целиком)")


if __name__ == "__main__":
    main()
