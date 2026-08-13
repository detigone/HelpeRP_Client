#!/usr/bin/env python3
"""Сборка HelpeRP.exe и подготовка папки dist/HelpeRP_Release."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD_CONFIG = ROOT / "core" / "build_config.py"
BUILD_CONFIG_DEV = '"""Флаг release-сборки. build_exe.py выставляет True перед PyInstaller."""\n\nRELEASE_BUILD = False\n'
BUILD_CONFIG_RELEASE = '"""Флаг release-сборки. build_exe.py выставляет True перед PyInstaller."""\n\nRELEASE_BUILD = True\n'


def _ensure_crypto():
    try:
        import cryptography  # noqa: F401
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])


def _ensure_signing_keys():
    subprocess.check_call(
        [sys.executable, str(ROOT / "tools" / "generate_license_key.py"), "--init-keys"],
        cwd=str(ROOT),
    )


def main():
    print("=== HelpeRP — сборка exe (release) ===\n")

    _ensure_crypto()
    _ensure_signing_keys()

    icon_script = ROOT / "tools" / "generate_icon.py"
    if icon_script.is_file():
        subprocess.check_call([sys.executable, str(icon_script)], cwd=str(ROOT))

    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("Устанавливаю PyInstaller…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    BUILD_CONFIG.write_text(BUILD_CONFIG_RELEASE, encoding="utf-8")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "PyInstaller", "--noconfirm", str(ROOT / "HelpeRP.spec")],
            cwd=str(ROOT),
        )
    finally:
        BUILD_CONFIG.write_text(BUILD_CONFIG_DEV, encoding="utf-8")

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

    print(f"\nГотово: {release}")
    print("  HelpeRP.exe  (RELEASE_BUILD=True, dev-bypass отключён)")
    print("  settings.json.example")
    print("\nКлючи: tools/.license_private.pem — НЕ отдавать покупателям!")


if __name__ == "__main__":
    main()
