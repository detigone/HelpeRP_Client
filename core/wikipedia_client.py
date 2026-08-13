"""Клиент Wikipedia / Wiktionary (ru) для HelpeRP."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from core.version import VERSION

WIKI_API = "https://ru.wikipedia.org/w/api.php"
WIKI_REST = "https://ru.wikipedia.org/api/rest_v1"
WIKTIONARY_API = "https://ru.wiktionary.org/w/api.php"

_HEADERS = {"User-Agent": f"HelpeRP/{VERSION} (RP knowledge client; contact: support@example.com)"}


def _get_json(url: str, timeout: float = 8.0) -> dict | list | None:
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def search_wikipedia(query: str, *, limit: int = 5) -> list[dict]:
    """Поиск статей ru.wikipedia.org."""
    params = urllib.parse.urlencode({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "format": "json",
        "utf8": 1,
    })
    data = _get_json(f"{WIKI_API}?{params}")
    if not data:
        return []

    results = []
    for hit in (data.get("query", {}) or {}).get("search", []):
        title = hit.get("title", "")
        snippet = _clean_html(hit.get("snippet", ""))
        if title:
            results.append({
                "title": title,
                "snippet": snippet,
                "url": f"https://ru.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}",
                "source": "Wikipedia",
            })
    return results


def get_wikipedia_summary(title: str, *, sentences: int = 4) -> dict | None:
    """Краткое описание статьи через REST API."""
    safe = urllib.parse.quote(title.replace(" ", "_"))
    url = f"{WIKI_REST}/page/summary/{safe}"
    data = _get_json(url)
    if not data or data.get("type") == "disambiguation":
        return None

    extract = (data.get("extract") or "").strip()
    if not extract:
        return None

    parts = extract.replace("...", ".").split(". ")
    text = ". ".join(parts[:sentences]).strip()
    if text and not text.endswith("."):
        text += "."

    return {
        "title": data.get("title") or title,
        "description": text,
        "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        "source": "Wikipedia",
    }


def search_wiktionary(term: str) -> dict | None:
    """Определение термина из Викисловаря."""
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": term,
        "prop": "extracts",
        "explaintext": 1,
        "exintro": 1,
        "format": "json",
    })
    data = _get_json(f"{WIKTIONARY_API}?{params}")
    if not data:
        return None

    pages = (data.get("query", {}) or {}).get("pages", {})
    for page in pages.values():
        if page.get("missing"):
            continue
        extract = (page.get("extract") or "").strip()
        if not extract:
            continue
        lines = [ln.strip() for ln in extract.splitlines() if ln.strip()]
        definition = lines[0][:600] if lines else extract[:600]
        title = page.get("title") or term
        return {
            "title": title,
            "description": definition,
            "url": f"https://ru.wiktionary.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}",
            "source": "Wiktionary",
        }
    return None


def lookup_term(query: str) -> str:
    """Комбинированный поиск: Wikipedia + Wiktionary."""
    q = (query or "").strip()
    if not q:
        return ""

    chunks: list[str] = []

    wiki = get_wikipedia_summary(q)
    if not wiki:
        hits = search_wikipedia(q, limit=1)
        if hits:
            wiki = get_wikipedia_summary(hits[0]["title"])
    if wiki:
        url = wiki.get("url") or ""
        chunks.append(f"**{wiki['title']}** (Wikipedia)\n{wiki['description']}")
        if url:
            chunks.append(f"Источник: {url}")

    wikt = search_wiktionary(q)
    if wikt and (not wiki or wikt["title"].lower() != wiki["title"].lower()):
        chunks.append(f"**{wikt['title']}** (Викисловарь)\n{wikt['description']}")
        if wikt.get("url"):
            chunks.append(f"Источник: {wikt['url']}")

    if not chunks:
        hits = search_wikipedia(q, limit=4)
        if hits:
            chunks.append("--- Wikipedia: похожие статьи ---")
            for h in hits:
                line = f"• {h['title']}"
                if h.get("snippet"):
                    line += f" — {h['snippet']}"
                chunks.append(line)

    return "\n\n".join(chunks)


def _clean_html(text: str) -> str:
    import re
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").strip()
