#!/usr/bin/env python3
"""Импорт статей из категории Wikipedia в terminology.json."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TERMS_FILE = ROOT / "data" / "terminology.json"
API = "https://ru.wikipedia.org/w/api.php"


def _api(params: dict) -> dict:
    params["format"] = "json"
    url = f"{API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "HelpeRP/1.0 WikipediaImporter"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def category_titles(category: str, limit: int) -> list[str]:
    titles: list[str] = []
    cmcontinue = None
    while len(titles) < limit:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": min(50, limit - len(titles)),
            "cmtype": "page",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        data = _api(params)
        members = (data.get("query", {}) or {}).get("categorymembers", [])
        for m in members:
            title = m.get("title", "")
            if title and ":" not in title.split()[0]:
                titles.append(title)
        cmcontinue = data.get("continue", {}).get("cmcontinue")
        if not cmcontinue:
            break
        time.sleep(0.2)
    return titles[:limit]


def fetch_summary(title: str) -> dict | None:
    safe = urllib.parse.quote(title.replace(" ", "_"))
    url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{safe}"
    req = urllib.request.Request(url, headers={"User-Agent": "HelpeRP/1.0 WikipediaImporter"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    extract = (data.get("extract") or "").strip()
    if not extract or data.get("type") == "disambiguation":
        return None
    return {
        "title": data.get("title") or title,
        "description": extract[:900],
        "category": "Wikipedia",
        "keywords": [w.lower() for w in title.split() if len(w) >= 3],
        "is_frequent": False,
        "wiki_url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
    }


def main():
    parser = argparse.ArgumentParser(description="Импорт категории Wikipedia в terminology.json")
    parser.add_argument("category", help="Название категории без префикса Category:")
    parser.add_argument("--limit", type=int, default=30, help="Макс. статей")
    parser.add_argument("--merge", action="store_true", help="Добавить к существующим, не заменять")
    args = parser.parse_args()

    if not TERMS_FILE.is_file():
        print("Сначала: py data/terminology_builder.py")
        sys.exit(1)

    with TERMS_FILE.open(encoding="utf-8") as f:
        data = json.load(f)

    print(f"Категория: {args.category} (до {args.limit} статей)")
    titles = category_titles(args.category, args.limit)
    print(f"Найдено заголовков: {len(titles)}")

    existing = {e.get("title", "").lower() for e in data.get("encyclopedia", [])}
    added = 0
    for title in titles:
        if title.lower() in existing:
            continue
        entry = fetch_summary(title)
        if not entry:
            continue
        data.setdefault("encyclopedia", []).append(entry)
        existing.add(title.lower())
        added += 1
        print(f"  + {title}")
        time.sleep(0.15)

    data["total_terms"] = len(data.get("dictionary", []))
    data["total_encyclopedia"] = len(data.get("encyclopedia", []))
    data["last_updated"] = time.strftime("%Y-%m-%d")

    with TERMS_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"\nГотово: добавлено {added} статей -> {TERMS_FILE}")


if __name__ == "__main__":
    main()
