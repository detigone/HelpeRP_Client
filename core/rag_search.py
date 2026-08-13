"""RAG-поиск (BM25) по базе HelpeRP — без тяжёлых ML-зависимостей."""

from __future__ import annotations

import math
import re
from collections import Counter

from core.search import item_blob

_TOKEN_RE = re.compile(r"[\w\d]+", re.UNICODE)
_BM25_K1 = 1.5
_BM25_B = 0.75


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


class RagSearcher:
    """BM25-индекс по списку записей базы."""

    def __init__(self):
        self._items: list[dict] = []
        self._doc_tokens: list[list[str]] = []
        self._doc_len: list[int] = []
        self._avg_dl = 0.0
        self._df: Counter[str] = Counter()
        self._N = 0

    def rebuild(self, items: list[dict]) -> None:
        self._items = list(items)
        self._doc_tokens = []
        self._doc_len = []
        self._df = Counter()

        for item in items:
            tokens = tokenize(item_blob(item))
            self._doc_tokens.append(tokens)
            self._doc_len.append(len(tokens))
            for t in set(tokens):
                self._df[t] += 1

        self._N = len(items)
        self._avg_dl = sum(self._doc_len) / self._N if self._N else 0.0

    def score(self, doc_idx: int, query: str) -> float:
        if not self._N or doc_idx >= self._N:
            return 0.0

        q_tokens = tokenize(query)
        if not q_tokens:
            return 0.0

        dl = self._doc_len[doc_idx]
        tf_map = Counter(self._doc_tokens[doc_idx])
        score = 0.0

        for term in q_tokens:
            if term not in self._df:
                continue
            df = self._df[term]
            idf = math.log(1 + (self._N - df + 0.5) / (df + 0.5))
            tf = tf_map.get(term, 0)
            denom = tf + _BM25_K1 * (1 - _BM25_B + _BM25_B * dl / (self._avg_dl or 1))
            score += idf * (tf * (_BM25_K1 + 1)) / (denom or 1)

        return score

    def search(self, query: str, *, top_k: int = 120) -> list[tuple[float, dict]]:
        if not query.strip() or not self._items:
            return []

        scored = [(self.score(i, query), self._items[i]) for i in range(self._N)]
        scored = [(s, item) for s, item in scored if s > 0]
        scored.sort(key=lambda x: (-x[0], not x[1].get("is_frequent", False), x[1].get("title", "")))
        return scored[:top_k]


_searcher = RagSearcher()
_items_ref: list[dict] | None = None


def get_rag_searcher() -> RagSearcher:
    return _searcher


def ensure_rag_index(items: list[dict]) -> RagSearcher:
    global _items_ref
    if _items_ref is not items or len(_searcher._items) != len(items):
        _searcher.rebuild(items)
        _items_ref = items
    return _searcher
