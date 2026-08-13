"""Автоматическое скачивание и установка обновлений HelpeRP."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from core.build_config import RELEASE_BUILD
from core.paths import app_dir, is_frozen
from core.updates import UpdateInfo
from core.version import VERSION


class UpdateInstallError(Exception):
    pass


def can_auto_install() -> bool:
    return is_frozen()


def _updates_root() -> Path:
    root = Path(app_dir()) / ".updates"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _cache_path(info: UpdateInfo) -> Path:
    return _updates_root() / "cache" / f"HelpeRP_{info.latest}.zip"


def _staging_path() -> Path:
    path = _updates_root() / "staging"
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _require_sha256(expected_sha256: str) -> str:
    digest = (expected_sha256 or "").strip().lower()
    if len(digest) != 64 or not all(c in "0123456789abcdef" for c in digest):
        raise UpdateInstallError("В manifest отсутствует корректная sha256")
    return digest


def verify_package(path: Path, expected_sha256: str = "") -> bool:
    if not path.is_file():
        return False
    if not expected_sha256:
        return not RELEASE_BUILD
    return _sha256_file(path).lower() == _require_sha256(expected_sha256)


def _allowed_download_url(url: str) -> bool:
    u = (url or "").strip()
    if u.startswith("https://"):
        return True
    if RELEASE_BUILD:
        return False
    return u.startswith("file://") or Path(u).is_file()


def _safe_extract_zip(zf: zipfile.ZipFile, dest: Path) -> None:
    dest = dest.resolve()
    for member in zf.infolist():
        name = member.filename.replace("\\", "/")
        if name.startswith("/") or ".." in Path(name).parts:
            raise UpdateInstallError(f"Небезопасный путь в архиве: {member.filename}")
        target = (dest / name).resolve()
        if dest not in target.parents and target != dest:
            raise UpdateInstallError(f"Zip Slip заблокирован: {member.filename}")
    zf.extractall(dest)


def _download_http(url: str, dest: Path, progress=None) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": f"HelpeRP/{VERSION} Updater"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        total = int(resp.headers.get("Content-Length") or 0)
        read = 0
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as out:
            while True:
                chunk = resp.read(256 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                read += len(chunk)
                if progress:
                    progress(read, total or read)


def _copy_local(src: Path, dest: Path, progress=None) -> None:
    total = src.stat().st_size
    dest.parent.mkdir(parents=True, exist_ok=True)
    read = 0
    with src.open("rb") as inp, dest.open("wb") as out:
        while True:
            chunk = inp.read(256 * 1024)
            if not chunk:
                break
            out.write(chunk)
            read += len(chunk)
            if progress:
                progress(read, total)


def download_update(info: UpdateInfo, progress=None, *, force: bool = False) -> Path:
    url = (info.download_url or "").strip()
    if not url:
        raise UpdateInstallError("В manifest не указан download_url")
    if not _allowed_download_url(url):
        raise UpdateInstallError("Разрешены только HTTPS-ссылки на обновления")

    digest = _require_sha256(info.sha256)
    dest = _cache_path(info)
    if dest.is_file() and not force and verify_package(dest, digest):
        if progress:
            progress(dest.stat().st_size, dest.stat().st_size)
        return dest

    if url.startswith("file://"):
        src = Path(url[7:])
        if not src.is_file():
            raise UpdateInstallError(f"Локальный файл не найден: {src}")
        _copy_local(src, dest, progress)
    elif url.startswith("https://"):
        _download_http(url, dest, progress)
    else:
        src = Path(url)
        if src.is_file():
            _copy_local(src, dest, progress)
        else:
            raise UpdateInstallError(f"Неподдерживаемый URL: {url}")

    if not verify_package(dest, digest):
        dest.unlink(missing_ok=True)
        raise UpdateInstallError("Контрольная сумма пакета не совпадает")

    return dest


def _find_release_root(staging: Path) -> Path:
    exe_files = list(staging.rglob("HelpeRP.exe"))
    if exe_files:
        return exe_files[0].parent
    items = [p for p in staging.iterdir() if p.name != "__MACOSX"]
    if len(items) == 1 and items[0].is_dir():
        nested = list(items[0].rglob("HelpeRP.exe"))
        if nested:
            return nested[0].parent
        return items[0]
    return staging


def prepare_install(package_path: Path) -> Path:
    if not package_path.is_file():
        raise UpdateInstallError("Пакет обновления не найден")

    staging = _staging_path()
    if package_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(package_path) as zf:
            _safe_extract_zip(zf, staging)
    elif package_path.name.lower() == "helperp.exe":
        shutil.copy2(package_path, staging / "HelpeRP.exe")
    else:
        raise UpdateInstallError("Ожидается .zip или HelpeRP.exe")

    root = _find_release_root(staging)
    if not (root / "HelpeRP.exe").is_file():
        raise UpdateInstallError("В пакете нет HelpeRP.exe")
    return root


def launch_install_and_exit(source_root: Path) -> None:
    if not can_auto_install():
        raise UpdateInstallError("Автоустановка доступна только в собранном exe")

    install_dir = Path(app_dir())
    marker = install_dir / ".updates" / "pending.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        f'{{"from":"{source_root.as_posix()}","version":"pending"}}',
        encoding="utf-8",
    )

    bat_path = install_dir / "_helperp_update.bat"
    bat = f"""@echo off
chcp 65001 >nul
timeout /t 2 /nobreak >nul
taskkill /F /IM HelpeRP.exe >nul 2>&1
xcopy /E /Y /I "{source_root}\\*" "{install_dir}\\"
del /Q "{install_dir}\\_helperp_update.bat" >nul 2>&1
start "" "{install_dir}\\HelpeRP.exe"
"""
    bat_path.write_text(bat, encoding="utf-8")

    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen(["cmd", "/c", str(bat_path)], creationflags=flags, close_fds=True)
    os._exit(0)


def install_update(package_path: Path) -> None:
    source = prepare_install(package_path)
    launch_install_and_exit(source)


def cached_update_path(info: UpdateInfo) -> Path | None:
    path = _cache_path(info)
    if path.is_file() and verify_package(path, info.sha256):
        return path
    return None
