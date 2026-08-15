"""Справочник мер и наказаний из законодательной базы."""

from __future__ import annotations

import re

from core.json_loader import clear_cache, load_json
from core.paths import data_dir
from core.search import filter_and_rank

# Справочник уровней розыска для RP-серверов
RP_LEVELS = [
    ("1", "Предупреждение / штраф", "Мелкое нарушение, устное замечание, штраф до 5 000 ₽."),
    ("2", "Задержание / доставление", "Доставление в ОВД, протокол, арест до 15 суток по КоАП."),
    ("3", "Арест / розыск", "Уголовное или серьёзное адм. дело, задержание, следствие."),
    ("4", "Ориентировка / обыск", "Розыск по базе, обыск, изъятие, блокировка счетов."),
    ("5", "Федеральный розыск", "ОПГ, тяжкие статьи, межрегиональная ориентировка."),
    ("6", "Особый режим", "Теракт, убийство сотрудника, ФСБ, закрытое дело, штурм."),
]

_cache: list[dict] | None = None


def _parse_level(punishment: str) -> int | None:
    if not punishment:
        return None
    m = re.search(r"(\d)\s*ур", punishment.lower())
    if m:
        return int(m.group(1))
    m = re.search(r"(\d)\s*–\s*(\d)\s*ур", punishment.lower())
    if m:
        return int(m.group(2))
    if "6 ур" in punishment.lower() or "6 уровень" in punishment.lower():
        return 6
    if "штраф" in punishment.lower() and "ур" not in punishment.lower():
        return 1
    return None


def load_measures() -> list[dict]:
    global _cache
    if _cache is not None:
        return _cache

    data = load_json(f"{data_dir()}/legislation_rf.json")
    if not isinstance(data, dict):
        _cache = []
        return _cache

    items: list[dict] = []
    for code_name, articles in data.get("codes", {}).items():
        if "Уголов" in code_name:
            kind = "uk"
            prefix = "УК"
        elif "КоАП" in code_name or "Административ" in code_name:
            kind = "koap"
            prefix = "КоАП"
        else:
            kind = "fz"
            prefix = "ФЗ"

        for a in articles:
            pun = a.get("punishment") or "—"
            items.append({
                "kind": kind,
                "prefix": prefix,
                "article": str(a.get("article", "")),
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "punishment": pun,
                "level": _parse_level(pun),
                "is_frequent": a.get("is_frequent", False),
                "keywords": a.get("keywords", []),
                "chapter": a.get("chapter", ""),
            })

    items.sort(key=lambda x: (
        {"uk": 0, "koap": 1, "fz": 2}.get(x["kind"], 9),
        x["article"],
    ))
    _cache = items
    return _cache


def filter_measures(
    items: list[dict],
    query: str = "",
    kind: str = "all",
    level: int | None = None,
    frequent_only: bool = False,
) -> list[dict]:
    pool = items
    if kind == "uk":
        pool = [x for x in pool if x["kind"] == "uk"]
    elif kind == "koap":
        pool = [x for x in pool if x["kind"] == "koap"]
    elif kind == "frequent":
        pool = [x for x in pool if x.get("is_frequent")]

    if level is not None:
        pool = [x for x in pool if x.get("level") == level]

    if frequent_only:
        pool = [x for x in pool if x.get("is_frequent")]

    if query:
        pool = filter_and_rank(pool, query)
    return pool


def invalidate_cache():
    global _cache
    _cache = None
    clear_cache()
