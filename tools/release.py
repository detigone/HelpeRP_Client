#!/usr/bin/env python3
"""Автоматический релиз HelpeRP: сборка, zip, manifest.json с sha256."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "core" / "version.py"
MANIFEST_FILE = ROOT / "updates" / "manifest.json"
RELEASES_DIR = ROOT / "dist" / "releases"


def read_version() -> str:
    text = VERSION_FILE.read_text(encoding="utf-8")
    m = re.search(r'^VERSION\s*=\s*["\']([^"\']+)["\']', text, re.M)
    if not m:
        raise SystemExit("Не найден VERSION в core/version.py")
    return m.group(1)


def write_version(version: str) -> None:
    text = VERSION_FILE.read_text(encoding="utf-8")
    text, n = re.subn(
        r'^VERSION\s*=\s*["\'][^"\']+["\']',
        f'VERSION = "{version}"',
        text,
        count=1,
        flags=re.M,
    )
    if not n:
        raise SystemExit("Не удалось обновить VERSION")
    VERSION_FILE.write_text(text, encoding="utf-8")


def bump_version(current: str, kind: str) -> str:
    parts = [int(x) for x in current.split(".")]
    while len(parts) < 3:
        parts.append(0)
    major, minor, patch = parts[:3]
    if kind == "major":
        major += 1
        minor = 0
        patch = 0
    elif kind == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_build() -> None:
    subprocess.check_call([sys.executable, str(ROOT / "tools" / "build_exe.py")], cwd=str(ROOT))


def create_release_zip(version: str) -> Path:
    source = ROOT / "dist" / "HelpeRP_Release"
    if not (source / "HelpeRP.exe").is_file():
        raise SystemExit("Сначала соберите exe: dist/HelpeRP_Release/HelpeRP.exe")

    RELEASES_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = RELEASES_DIR / f"HelpeRP_{version}.zip"

    if zip_path.is_file():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in source.rglob("*"):
            if file.is_file():
                arc = Path("HelpeRP_Release") / file.relative_to(source)
                zf.write(file, arc.as_posix())

    return zip_path


def read_manifest_url() -> str:
    text = VERSION_FILE.read_text(encoding="utf-8")
    m = re.search(r'^UPDATE_MANIFEST_URL\s*=\s*["\']([^"\']+)["\']', text, re.M)
    return m.group(1) if m else "https://example.com/helperp/updates/manifest.json"


def derive_download_url(manifest_url: str, version: str) -> str:
    repo = os.environ.get("GITHUB_REPOSITORY")
    if repo:
        user, name = repo.split("/", 1)
        return f"https://github.com/{repo}/releases/download/v{version}/HelpeRP_{version}.zip"
    if "github.io" in manifest_url:
        base = manifest_url.split("/updates/")[0]
        return f"{base}/releases/HelpeRP_{version}.zip"
    base = manifest_url.rsplit("/", 1)[0]
    if "example.com" in base:
        return f"{base.replace('/updates', '')}/releases/HelpeRP_{version}.zip"
    return f"{base}/HelpeRP_{version}.zip"


def write_manifest(
    version: str,
    zip_path: Path,
    *,
    changelog: str,
    download_url: str | None = None,
) -> dict:
    digest = sha256_file(zip_path)
    size = zip_path.stat().st_size
    url = download_url or derive_download_url(read_manifest_url(), version)

    data = {
        "version": version,
        "released": date.today().isoformat(),
        "title": f"HelpeRP {version}",
        "required": False,
        "min_app_version": "1.0.0",
        "download_url": url,
        "sha256": digest,
        "file_size": size,
        "changelog": changelog.strip() or f"HelpeRP {version}",
    }
    sys.path.insert(0, str(ROOT))
    from tools.signing_private import ensure_keypair, sign_manifest

    ensure_keypair()
    data["signature"] = sign_manifest(data)
    MANIFEST_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")

    publish_manifest = RELEASES_DIR / "manifest.json"
    shutil.copy2(MANIFEST_FILE, publish_manifest)
    return data


def load_changelog(path: Path | None, version: str) -> str:
    if path and path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return (
        f"HelpeRP {version}\n\n"
        "• Автоматическая сборка релиза\n"
        "• Автообновление и установка в один клик\n"
        "• manifest.json с контрольной суммой sha256"
    )


def main():
    parser = argparse.ArgumentParser(description="Автоматический релиз HelpeRP")
    parser.add_argument("--bump", choices=("patch", "minor", "major"), help="Поднять версию перед сборкой")
    parser.add_argument("--version", help="Задать версию вручную")
    parser.add_argument("--changelog", default="", help="Текст changelog")
    parser.add_argument("--changelog-file", type=Path, help="Файл changelog")
    parser.add_argument("--download-url", help="Прямой URL zip-пакета")
    parser.add_argument("--skip-build", action="store_true", help="Не собирать exe (только zip+manifest)")
    args = parser.parse_args()

    version = read_version()
    if args.version:
        version = args.version
        write_version(version)
    elif args.bump:
        version = bump_version(version, args.bump)
        write_version(version)
        print(f"Версия: {version}")

    if not args.skip_build:
        print("\n=== Сборка exe ===")
        run_build()

    print("\n=== Архив релиза ===")
    zip_path = create_release_zip(version)
    print(f"  {zip_path}")

    changelog = args.changelog or load_changelog(args.changelog_file, version)
    manifest = write_manifest(
        version, zip_path, changelog=changelog, download_url=args.download_url,
    )

    print("\n=== manifest.json ===")
    print(f"  version:      {manifest['version']}")
    print(f"  download_url: {manifest['download_url']}")
    print(f"  sha256:       {manifest['sha256'][:16]}…")
    print(f"  file_size:    {manifest['file_size']:,} bytes")
    print(f"\nГотово. Загрузите на сервер:")
    print(f"  {zip_path.name}")
    print(f"  {MANIFEST_FILE.relative_to(ROOT)}  ->  {read_manifest_url()}")


if __name__ == "__main__":
    main()
