"""Профили персонажей HelpeRP."""

from __future__ import annotations

import copy
import uuid

DEFAULT_CHARACTER = {
    "name": "Иван Иванов",
    "rank": "Рядовой",
    "badge": "№0000",
    "personality": "Вежливый, строго следует уставу, говорит уверенно",
}


def _new_id() -> str:
    return f"char_{uuid.uuid4().hex[:8]}"


def migrate_characters_settings(settings: dict) -> dict:
    """Перенос legacy character → characters[]."""
    if settings.get("characters"):
        if not settings.get("active_character_id") and settings["characters"]:
            settings["active_character_id"] = settings["characters"][0]["id"]
        return settings

    old = settings.get("character") or {}
    merged = {**DEFAULT_CHARACTER, **old}
    cid = _new_id()
    settings["characters"] = [{
        "id": cid,
        "label": "Основной",
        "name": merged.get("name", ""),
        "rank": merged.get("rank", ""),
        "badge": merged.get("badge", ""),
        "personality": merged.get("personality", ""),
    }]
    settings["active_character_id"] = cid
    settings["character"] = {
        "name": merged.get("name", ""),
        "rank": merged.get("rank", ""),
        "badge": merged.get("badge", ""),
        "personality": merged.get("personality", ""),
    }
    return settings


def _cfg():
    from core.config import app_config
    return app_config


def list_characters() -> list[dict]:
    return list(_cfg().get("characters", []) or [])


def get_active_character() -> dict:
    chars = list_characters()
    active_id = _cfg().get("active_character_id", "")
    for c in chars:
        if c.get("id") == active_id:
            return copy.deepcopy(c)
    if chars:
        return copy.deepcopy(chars[0])
    return {"id": "", "label": "Основной", **DEFAULT_CHARACTER}


def get_active_character_dict() -> dict:
    """Формат для ИИ и legacy character."""
    c = get_active_character()
    return {
        "name": c.get("name", ""),
        "rank": c.get("rank", ""),
        "badge": c.get("badge", ""),
        "personality": c.get("personality", ""),
    }


def set_active_character(char_id: str) -> bool:
    chars = list_characters()
    if not any(c.get("id") == char_id for c in chars):
        return False
    cfg = _cfg()
    cfg.set("active_character_id", char_id)
    cfg.set("character", get_active_character_dict())
    return True


def save_character(profile: dict) -> dict:
    cfg = _cfg()
    chars = list_characters()
    pid = profile.get("id") or _new_id()
    entry = {
        "id": pid,
        "label": (profile.get("label") or profile.get("name") or "Персонаж").strip(),
        "name": profile.get("name", "").strip(),
        "rank": profile.get("rank", "").strip(),
        "badge": profile.get("badge", "").strip(),
        "personality": profile.get("personality", "").strip(),
    }

    updated = False
    for i, c in enumerate(chars):
        if c.get("id") == pid:
            chars[i] = entry
            updated = True
            break
    if not updated:
        chars.append(entry)

    cfg.set("characters", chars)
    if cfg.get("active_character_id") == pid or len(chars) == 1:
        cfg.set("active_character_id", pid)
        cfg.set("character", get_active_character_dict())
    return entry


def delete_character(char_id: str) -> bool:
    cfg = _cfg()
    chars = [c for c in list_characters() if c.get("id") != char_id]
    if len(chars) == len(list_characters()):
        return False
    if not chars:
        return False
    cfg.set("characters", chars)
    if cfg.get("active_character_id") == char_id:
        cfg.set("active_character_id", chars[0]["id"])
        cfg.set("character", {
            "name": chars[0].get("name", ""),
            "rank": chars[0].get("rank", ""),
            "badge": chars[0].get("badge", ""),
            "personality": chars[0].get("personality", ""),
        })
    return True


def character_labels() -> list[str]:
    return [f"{c.get('label', c.get('name', 'Персонаж'))}" for c in list_characters()]


def character_id_by_label(label: str) -> str | None:
    for c in list_characters():
        if c.get("label") == label or c.get("name") == label:
            return c.get("id")
    return None
