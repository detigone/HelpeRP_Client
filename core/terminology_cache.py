"""Кэш терминов из Wikipedia — накапливается при онлайн-поиске."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from core.paths import app_dir

_CACHE_FILE = "terminology_cache.json"
_MAX_ENTRIES = 500


def _cache_path() -> str:
    folder = os.path.join(app_dir(), ".cache")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, _CACHE_FILE)


def load_cache() -> list[dict]:
    path = _cache_path()
    if not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_cache(entries: list[dict]) -> None:
    path = _cache_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entries[:_MAX_ENTRIES], f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[TerminologyCache] save: {e}")


def remember_term(title: str, description: str, *, source: str = "Wikipedia", url: str = ""):
    title = (title or "").strip()
    description = (description or "").strip()
    if not title or not description:
        return

    entries = load_cache()
    key = title.lower()
    for entry in entries:
        if entry.get("title", "").lower() == key:
            entry["description"] = description
            entry["updated"] = datetime.now(timezone.utc).isoformat()
            if url:
                entry["url"] = url
            save_cache(entries)
            return

    entries.insert(0, {
        "title": title,
        "description": description,
        "source": source,
        "url": url,
        "updated": datetime.now(timezone.utc).isoformat(),
        "keywords": [w.lower() for w in title.split() if len(w) >= 3],
    })
    save_cache(entries)


def search_cache(query: str) -> list[dict]:
    q = (query or "").strip().lower()
    if not q:
        return []
    results = []
    for entry in load_cache():
        blob = f"{entry.get('title', '')} {entry.get('description', '')}".lower()
        if q in blob or any(w in blob for w in q.split() if len(w) >= 3):
            results.append({
                "title": entry.get("title", ""),
                "description": entry.get("description", ""),
                "category": f"Кэш · {entry.get('source', 'Wikipedia')}",
                "keywords": entry.get("keywords", []),
                "is_frequent": False,
            })
    return results[:8]
