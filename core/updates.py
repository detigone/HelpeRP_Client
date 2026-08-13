"""Проверка онлайн-обновлений HelpeRP."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

from core.config import app_config
from core.paths import bundle_dir
from core.version import UPDATE_MANIFEST_URL, VERSION


@dataclass
class UpdateInfo:
    available: bool
    current: str
    latest: str
    title: str
    changelog: str
    download_url: str
    released: str
    required: bool
    sha256: str = ""
    file_size: int = 0
    source: str = "online"

    def to_dict(self) -> dict:
        return {
            "available": self.available,
            "current": self.current,
            "latest": self.latest,
            "title": self.title,
            "changelog": self.changelog,
            "download_url": self.download_url,
            "released": self.released,
            "required": self.required,
            "sha256": self.sha256,
            "file_size": self.file_size,
            "source": self.source,
        }


def parse_version(value: str) -> tuple[int, ...]:
    parts: list[int] = []
    for chunk in (value or "0").strip().split("."):
        try:
            parts.append(int(chunk.split("-")[0].split("_")[0]))
        except ValueError:
            parts.append(0)
    return tuple(parts) if parts else (0,)


def is_newer(remote: str, local: str) -> bool:
    return parse_version(remote) > parse_version(local)


def _manifest_url() -> str:
    cfg = app_config.get("updates", {}) or {}
    return (cfg.get("manifest_url") or "").strip() or UPDATE_MANIFEST_URL


def _fetch_url(url: str, timeout: float = 8.0) -> dict | None:
    try:
        if url.startswith("file://"):
            path = url[7:]
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"HelpeRP/{VERSION} UpdateChecker"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def _load_bundled_manifest() -> dict | None:
    path = os.path.join(bundle_dir(), "updates", "manifest.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _parse_manifest(data: dict, source: str) -> UpdateInfo | None:
    if not data:
        return None
    latest = str(data.get("version", "")).strip()
    if not latest:
        return None

    dismissed = (app_config.get("updates", {}) or {}).get("dismissed_version", "")
    available = is_newer(latest, VERSION) and latest != dismissed

    return UpdateInfo(
        available=available,
        current=VERSION,
        latest=latest,
        title=str(data.get("title") or f"HelpeRP {latest}"),
        changelog=str(data.get("changelog") or "Список изменений не указан."),
        download_url=str(data.get("download_url") or ""),
        released=str(data.get("released") or ""),
        required=bool(data.get("required", False)),
        sha256=str(data.get("sha256") or ""),
        file_size=int(data.get("file_size") or 0),
        source=source,
    )


def should_check_now() -> bool:
    cfg = app_config.get("updates", {}) or {}
    if not cfg.get("auto_check", True):
        return False

    last = cfg.get("last_check")
    if not last:
        return True

    try:
        last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        hours = int(cfg.get("check_interval_hours", 24))
        delta = datetime.now(timezone.utc) - last_dt.astimezone(timezone.utc)
        return delta.total_seconds() >= hours * 3600
    except (ValueError, TypeError):
        return True


def mark_checked():
    cfg = dict(app_config.get("updates", {}) or {})
    cfg["last_check"] = datetime.now(timezone.utc).isoformat()
    app_config.set("updates", cfg)


def dismiss_version(version: str):
    cfg = dict(app_config.get("updates", {}) or {})
    cfg["dismissed_version"] = version
    app_config.set("updates", cfg)


def check_for_updates(*, force: bool = False) -> UpdateInfo | None:
    """Проверяет обновления. force=True игнорирует интервал."""
    if not force and not should_check_now():
        return None

    mark_checked()
    url = _manifest_url()

    data = _fetch_url(url)
    if data:
        return _parse_manifest(data, "online")

    data = _load_bundled_manifest()
    if data:
        info = _parse_manifest(data, "bundled")
        if info:
            info.available = False  # bundled — только fallback, не уведомляем
        return info

    return None


def get_update_status_text(info: UpdateInfo | None) -> str:
    if not info:
        return f"Версия {VERSION} · проверка пропущена или сервер недоступен"
    if info.available:
        return f"Доступно обновление {info.latest} (у вас {info.current})"
    if info.source == "bundled":
        return f"Версия {info.current} · онлайн-проверка недоступна"
    return f"Установлена актуальная версия {info.current}"
