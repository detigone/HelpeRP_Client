# HelpeRP_Client/core/online_search.py
"""Онлайн-поиск: DuckDuckGo + Wikipedia + Wiktionary."""

import json
import urllib.parse
import urllib.request

from core.config import app_config
from core.terminology_cache import remember_term, search_cache
from core.wikipedia_client import lookup_term


def _wikipedia_enabled() -> bool:
    return bool(app_config.get("search", {}).get("wikipedia", True))


def search_law_online(query: str, faction_context: str = "Законодательство РФ") -> str:
    q = (query or "").strip()
    if not q:
        return ""

    chunks: list[str] = []

    cached = search_cache(q)
    if cached:
        chunks.append("--- Сохранённые термины ---")
        for item in cached[:3]:
            chunks.append(f"• {item['title']}: {item['description'][:280]}")

    if _wikipedia_enabled():
        wiki_text = lookup_term(q)
        if wiki_text:
            chunks.append("--- Wikipedia / Викисловарь ---")
            chunks.append(wiki_text)
            _cache_wikipedia_result(q, wiki_text)

    ddg = _search_duckduckgo(f"{faction_context} {q} RP закон протокол")
    if ddg:
        chunks.append(ddg)

    return "\n\n".join(chunks) if chunks else ""


def _cache_wikipedia_result(query: str, text: str):
    """Сохраняет первую найденную Wikipedia-статью в локальный кэш."""
    lines = text.splitlines()
    title = query
    body_parts: list[str] = []
    url = ""
    for line in lines:
        if line.startswith("**") and "**" in line[2:]:
            title = line.strip("*").split("**")[0].strip()
            if "(Wikipedia)" in line:
                title = title.replace("(Wikipedia)", "").strip()
        elif line.startswith("Источник: http"):
            url = line.replace("Источник:", "").strip()
        elif line and not line.startswith("---"):
            body_parts.append(line)
    description = " ".join(body_parts)[:800]
    if description:
        remember_term(title, description, source="Wikipedia", url=url)


def _search_duckduckgo(full_query: str) -> str:
    encoded = urllib.parse.quote(full_query)
    url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "HelpeRP/1.0 (RP knowledge client)"},
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        chunks = []
        abstract = (data.get("AbstractText") or "").strip()
        if abstract:
            src = data.get("AbstractSource") or "DuckDuckGo"
            chunks.append(f"{abstract}\n(Источник: {src})")

        for topic in (data.get("RelatedTopics") or [])[:4]:
            if isinstance(topic, dict):
                text = topic.get("Text") or ""
                if text:
                    chunks.append(text)
            elif isinstance(topic, dict) and "Topics" in topic:
                for sub in topic.get("Topics", [])[:2]:
                    t = sub.get("Text") if isinstance(sub, dict) else ""
                    if t:
                        chunks.append(t)

        if not chunks:
            return _search_html_lite(full_query)

        return "--- DuckDuckGo ---\n\n" + "\n\n• ".join(chunks[:5])

    except Exception as e:
        print(f"[Online Search] API: {e}")
        return _search_html_lite(full_query)


def _search_html_lite(query: str) -> str:
    """Fallback: DuckDuckGo Lite HTML."""
    import re

    encoded = urllib.parse.quote(query)
    url = f"https://lite.duckduckgo.com/lite/?q={encoded}"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        snippets = re.findall(
            r'<td class="result-snippet".*?>(.*?)</td>', html, re.DOTALL | re.IGNORECASE
        )
        if not snippets:
            snippets = re.findall(r'class="result-snippet"[^>]*>(.*?)</', html, re.DOTALL)

        clean = []
        for snip in snippets[:4]:
            text = re.sub(r"<[^>]+>", "", snip)
            text = text.replace("&quot;", '"').replace("&amp;", "&").strip()
            if text:
                clean.append(text)

        if not clean:
            return ""

        return "--- DuckDuckGo ---\n\n" + "\n\n• ".join(clean)
    except Exception as e:
        print(f"[Online Search] Lite HTML: {e}")
        return ""
