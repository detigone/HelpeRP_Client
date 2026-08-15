"""Ранжированный поиск по записям баз HelpeRP."""

from __future__ import annotations

from core.config import app_config


def item_blob(item: dict) -> str:
    parts = [
        str(item.get("article", "")),
        item.get("title", ""),
        item.get("description", ""),
        item.get("protocol", ""),
        item.get("category", ""),
        item.get("chapter", ""),
        item.get("punishment", ""),
        item.get("code_name", ""),
        item.get("source_faction", ""),
        " ".join(item.get("keywords", [])),
        " ".join(item.get("usable_by", [])),
    ]
    return " ".join(p for p in parts if p).lower()


def score_item(item: dict, query: str) -> float:
    """Чем выше — тем релевантнее. 0 = не подходит."""
    if not query:
        return 1.0

    q = query.lower().strip()
    blob = item_blob(item)
    if not q:
        return 0.0

    # Точное совпадение номера статьи
    art = str(item.get("article", "")).lower()
    if art and (q == art or q == f"ст {art}" or q == f"ст. {art}"):
        return 1000.0

    if q in blob:
        base = 50.0
    else:
        words = [w for w in q.split() if len(w) >= 2]
        if not words:
            return 0.0
        hits = sum(1 for w in words if w in blob)
        if hits == 0:
            return 0.0
        base = 10.0 * hits / len(words)

    title = (item.get("title") or "").lower()
    if q in title:
        base += 30.0
    for w in q.split():
        if len(w) >= 3 and w in title:
            base += 8.0

    keywords = " ".join(item.get("keywords", [])).lower()
    for w in q.split():
        if len(w) >= 3 and w in keywords:
            base += 12.0

    if item.get("is_frequent"):
        base += 3.0

    return base


def _sort_scored(scored: list[tuple[float, dict]]) -> list[dict]:
    """Отсортировать (score, item) и вернуть список записей."""
    scored.sort(key=lambda x: (-x[0], not x[1].get("is_frequent", False), x[1].get("title", "")))
    return [item for _, item in scored]


def filter_and_rank(items: list[dict], query: str) -> list[dict]:
    query = (query or "").strip()
    if not query:
        return list(items)

    use_rag = True
    try:
        use_rag = bool(app_config.get("search", {}).get("rag", True))
    except Exception:
        pass

    if use_rag and len(query) >= 2:
        return hybrid_filter_and_rank(items, query)

    return _keyword_filter_and_rank(items, query)


def _keyword_filter_and_rank(items: list[dict], query: str) -> list[dict]:
    query = query.lower().strip()
    scored = []
    for item in items:
        s = score_item(item, query)
        if s > 0:
            scored.append((s, item))

    return _sort_scored(scored)


def hybrid_filter_and_rank(items: list[dict], query: str) -> list[dict]:
    """Ключевые слова + BM25 (RAG)."""
    from core.rag_search import ensure_rag_index

    q = query.lower().strip()
    rag = ensure_rag_index(items)
    rag_map = {id(item): score for score, item in rag.search(q, top_k=len(items))}

    scored = []
    for item in items:
        kw = score_item(item, q)
        bm25 = rag_map.get(id(item), 0.0)
        total = kw + bm25 * 12.0
        if total > 0:
            scored.append((total, item))

    if not scored:
        return [item for _, item in rag.search(q, top_k=80)]

    return _sort_scored(scored)
