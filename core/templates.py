"""Загрузка и поиск шаблонов отыгровок (без ИИ)."""

from __future__ import annotations

import json
import os

from core.paths import data_dir
from core.search import filter_and_rank

_TEMPLATES: list[dict] | None = None


def _path() -> str:
    return os.path.join(data_dir(), "templates.json")


def load_templates() -> list[dict]:
    global _TEMPLATES
    if _TEMPLATES is not None:
        return _TEMPLATES

    path = _path()
    if not os.path.isfile(path):
        _TEMPLATES = []
        return _TEMPLATES

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    items = []
    for t in data.get("templates", []):
        item = dict(t)
        item.setdefault("category", t.get("category", "Общее"))
        item.setdefault("description", "\n".join(t.get("lines", [])))
        item["keywords"] = list(t.get("tags", [])) + [t.get("faction", ""), t.get("title", "")]
        item["is_frequent"] = bool(t.get("is_frequent", False))
        
        # Preserve new v2.0 template fields
        if "variations" not in item:
            item["variations"] = t.get("variations", [])
        if "success_outcome" not in item:
            item["success_outcome"] = t.get("success_outcome", "")
        if "fail_outcome" not in item:
            item["fail_outcome"] = t.get("fail_outcome", "")
        if "advice" not in item:
            item["advice"] = t.get("advice", "")
        
        items.append(item)

    _TEMPLATES = items
    return items


def filter_templates(query: str = "", faction: str = "Все") -> list[dict]:
    pool = load_templates()
    if faction and faction != "Все":
        pool = [t for t in pool if t.get("faction", "") == faction or faction in (t.get("faction") or "")]
    if query.strip():
        return filter_and_rank(pool, query)
    pool.sort(key=lambda x: (not x.get("is_frequent", False), x.get("title", "")))
    return pool


def template_to_text(template: dict) -> str:
    """Format template with all fields (v2.0+ support)."""
    parts = []
    
    # Main lines
    lines = template.get("lines") or []
    if lines:
        parts.append("\n".join(lines))
    
    # Variations
    variations = template.get("variations") or []
    if variations:
        parts.append("\n")
        for var in variations:
            condition = var.get("condition", "")
            var_lines = var.get("lines", [])
            if condition:
                parts.append(f"[{condition}]")
            if var_lines:
                parts.append("\n".join(var_lines))
    
    # Outcomes
    success = template.get("success_outcome", "")
    fail = template.get("fail_outcome", "")
    if success or fail:
        parts.append("\n")
        if success:
            parts.append(f"✓ Успех: {success}")
        if fail:
            parts.append(f"✗ Неудача: {fail}")
    
    # Advice
    advice = template.get("advice", "")
    if advice:
        parts.append("\n")
        parts.append(f"💡 Совет: {advice}")
    
    return "\n".join(filter(None, parts))


def invalidate_cache():
    global _TEMPLATES
    _TEMPLATES = None
