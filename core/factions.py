"""Реестр фракций HelpeRP: файлы данных, темы, загрузка."""

import json
import os

from core.paths import data_dir

DATA_DIR = data_dir()

FACTIONS = [
    {
        "id": "all",
        "name": "Все базы",
        "file": None,
        "icon": "📚",
        "icon_file": "logo.png",
        "accent": "#a78bfa",
        "accent_hover": "#c4b5fd",
        "subtitle": "Объединённый поиск по всем фракциям",
        "entry_label": "записей",
    },
    {
        "id": "legislation",
        "name": "Законодательство РФ",
        "file": "legislation_rf.json",
        "icon": "⚖",
        "icon_file": "rules.png",
        "accent": "#4a9eff",
        "accent_hover": "#6bb3ff",
        "subtitle": "УК · КоАП · ФЗ · УПК",
        "entry_label": "статей",
    },
    {
        "id": "mvd",
        "name": "МВД",
        "file": "mvd.json",
        "icon": "🚔",
        "icon_file": "moderator.png",
        "accent": "#2563eb",
        "accent_hover": "#3b82f6",
        "subtitle": "Устав · Патруль · Задержание",
        "entry_label": "регламентов",
    },
    {
        "id": "fsb",
        "name": "ФСБ",
        "file": "fsb.json",
        "icon": "🛡",
        "icon_file": "admin.png",
        "accent": "#b91c1c",
        "accent_hover": "#dc2626",
        "subtitle": "Госбезопасность · КТО · ОРМ",
        "entry_label": "регламентов",
    },
    {
        "id": "sk",
        "name": "Следственный комитет",
        "file": "sk.json",
        "icon": "🔍",
        "icon_file": "editor.png",
        "accent": "#7c3aed",
        "accent_hover": "#8b5cf6",
        "subtitle": "Следствие · Экспертизы · Допрос",
        "entry_label": "регламентов",
    },
    {
        "id": "prokuratura",
        "name": "Прокуратура",
        "file": "prokuratura.json",
        "icon": "📋",
        "icon_file": "management.png",
        "accent": "#1e3a5f",
        "accent_hover": "#2563eb",
        "subtitle": "Надзор · Санкции · Обжалование",
        "entry_label": "регламентов",
    },
    {
        "id": "rosgvardia",
        "name": "Росгвардия",
        "file": "rosgvardia.json",
        "icon": "⭐",
        "icon_file": "star.png",
        "accent": "#ca8a04",
        "accent_hover": "#eab308",
        "subtitle": "Оцепление · Охрана · КТО",
        "entry_label": "регламентов",
    },
    {
        "id": "fsin",
        "name": "ФСИН",
        "file": "fsin.json",
        "icon": "🔒",
        "icon_file": "owner.png",
        "accent": "#52525b",
        "accent_hover": "#71717a",
        "subtitle": "Колония · Досмотр · Режим",
        "entry_label": "регламентов",
    },
    {
        "id": "mchs",
        "name": "МЧС",
        "file": "mchs.json",
        "icon": "🔥",
        "icon_file": "fire.png",
        "accent": "#ea580c",
        "accent_hover": "#f97316",
        "subtitle": "Пожар · АСР · РХБЗ",
        "entry_label": "протоколов",
    },
    {
        "id": "smp",
        "name": "СМП",
        "file": "smp.json",
        "icon": "🏥",
        "icon_file": "support.png",
        "accent": "#059669",
        "accent_hover": "#10b981",
        "subtitle": "СЛР · Травмы · Реанимация",
        "entry_label": "протоколов",
    },
    {
        "id": "smi",
        "name": "СМИ",
        "file": "smi.json",
        "icon": "📺",
        "icon_file": "web.png",
        "accent": "#d97706",
        "accent_hover": "#f59e0b",
        "subtitle": "ПРО · Эфир · Реклама",
        "entry_label": "регламентов",
    },
    {
        "id": "army",
        "name": "Армия",
        "file": "army.json",
        "icon": "🎖",
        "icon_file": "developer.png",
        "accent": "#4d7c0f",
        "accent_hover": "#65a30d",
        "subtitle": "Устав · КПП · Наряды",
        "entry_label": "регламентов",
    },
    {
        "id": "terminology",
        "name": "Энциклопедия",
        "file": "terminology.json",
        "icon": "📖",
        "icon_file": "logo.png",
        "accent": "#7c3aed",
        "accent_hover": "#8b5cf6",
        "subtitle": "Термины · Wikipedia · RP-словарь",
        "entry_label": "терминов",
    },
    {
        "id": "crime",
        "name": "Крайм / ОПГ",
        "file": "crime.json",
        "icon": "💀",
        "icon_file": "punishment.png",
        "accent": "#9333ea",
        "accent_hover": "#a855f7",
        "subtitle": "Ограбления · Переговоры · Отмыв",
        "entry_label": "сценариев",
    },
]

FACTION_BY_NAME = {f["name"]: f for f in FACTIONS}
FACTION_NAMES = [f["name"] for f in FACTIONS]


def get_faction(name):
    return FACTION_BY_NAME.get(name, FACTIONS[0])


def get_faction_by_id(faction_id):
    """Найти фракцию по id (для эмодзи-иконок в UI)."""
    for fac in FACTIONS:
        if fac.get("id") == faction_id:
            return fac
    return FACTIONS[0]


def _code_prefix(code_name):
    if "Уголов" in code_name:
        return "УК"
    if "Административ" in code_name or "КоАП" in code_name:
        return "КоАП"
    if "Федераль" in code_name or "УПК" in code_name or "ФЗ" in code_name:
        return "ФЗ"
    return code_name[:8]


def _dict_to_item(entry):
    short = entry["short"]
    full = entry["full"]
    preview = full[:55] + ("…" if len(full) > 55 else "")
    return {
        "title": f"{short} — {preview}",
        "description": full,
        "is_frequent": entry.get("is_frequent", False),
        "category": entry.get("category") or "Словарь терминов",
        "keywords": entry.get("keywords") or [short.lower(), full.lower()],
    }


def _normalize_entry(raw, prefix=""):
    item = dict(raw)
    title = raw.get("title", "Без названия")
    if prefix:
        item["title"] = f"[{prefix}] {title}"
    elif not title.startswith("["):
        item["title"] = title
    return item


def _load_single_faction_file(faction):
    path = os.path.join(DATA_DIR, faction["file"])
    if not os.path.exists(path):
        return [], faction

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = []
    if "codes" in data:
        for c_name, arts in data["codes"].items():
            prefix = _code_prefix(c_name)
            for a in arts:
                items.append(_normalize_entry(a, prefix))
                items[-1]["code_name"] = c_name

    for key in ("regulations", "emergency_protocols", "medical_protocols", "scenarios"):
        if key in data:
            for entry in data[key]:
                items.append(_normalize_entry(entry))

    for d in data.get("dictionary", []):
        items.append(_dict_to_item(d))

    for entry in data.get("encyclopedia", []):
        items.append(_normalize_entry(entry))

    items.sort(key=lambda x: (not x.get("is_frequent", False), x.get("title", "")))
    return items, faction


def load_all_items():
    """Объединяет записи всех фракций."""
    merged = []
    for fac in FACTIONS:
        if fac["id"] == "all" or not fac.get("file"):
            continue
        items, _ = _load_single_faction_file(fac)
        tag = fac["name"][:4]
        for item in items:
            tagged = dict(item)
            tagged["source_faction"] = fac["name"]
            if f"[{tag}]" not in tagged.get("title", ""):
                tagged["title"] = f"[{fac['icon']}{tag}] {tagged['title']}"
            merged.append(tagged)
    merged.sort(key=lambda x: (not x.get("is_frequent", False), x.get("title", "")))
    return merged, get_faction("Все базы")


def load_faction_items(faction_name):
    """Загружает и нормализует все записи базы выбранной фракции."""
    if faction_name == "Все базы":
        return load_all_items()

    faction = get_faction(faction_name)
    if not faction.get("file"):
        return load_all_items()

    items, fac = _load_single_faction_file(faction)

    if faction["id"] == "terminology":
        try:
            from core.terminology_cache import load_cache
            for entry in load_cache():
                items.insert(0, {
                    "title": f"[Кэш] {entry.get('title', '')}",
                    "description": entry.get("description", ""),
                    "category": f"Кэш · {entry.get('source', 'Wikipedia')}",
                    "keywords": entry.get("keywords", []),
                    "is_frequent": False,
                })
        except Exception:
            pass

    return items, fac
