"""Пресеты оформления HelpeRP v2 — соответствуют новой теме."""

from __future__ import annotations

# id → palette (ключи совпадают с полями gui.theme)
PRESETS: dict[str, dict] = {
    "helperp": {
        "label": "HelpeRP Purple",
        "accent": "#7c3aed",
        "accent_hover": "#8b5cf6",
        "bg_root": "#0a0812",
        "bg_sidebar": "#110e1a",
        "bg_panel": "#161222",
        "bg_card": "#1e1830",
        "bg_input": "#221c36",
        "bg_hover": "#2a2240",
        "bg_selected": "#322848",
        "border": "#3d3258",
        "border_light": "#4c4070",
        "text_primary": "#f5f3ff",
        "text_secondary": "#b8b0d0",
        "text_muted": "#7a7194",
    },
    "midnight": {
        "label": "Полночь",
        "accent": "#6366f1",
        "accent_hover": "#818cf8",
        "bg_root": "#050608",
        "bg_sidebar": "#0a0b0f",
        "bg_panel": "#0f1117",
        "bg_card": "#151820",
        "bg_input": "#1a1d26",
        "bg_hover": "#22262f",
        "bg_selected": "#2a2f3a",
        "border": "#252a35",
        "border_light": "#353b48",
        "text_primary": "#eef0f4",
        "text_secondary": "#9aa3b2",
        "text_muted": "#5c6578",
    },
    "ocean": {
        "label": "Океан",
        "accent": "#06b6d4",
        "accent_hover": "#22d3ee",
        "bg_root": "#061018",
        "bg_sidebar": "#0a1620",
        "bg_panel": "#0e1c28",
        "bg_card": "#122430",
        "bg_input": "#162a38",
        "bg_hover": "#1c3444",
        "bg_selected": "#224050",
        "border": "#2a4a5c",
        "border_light": "#3a6070",
        "text_primary": "#ecfeff",
        "text_secondary": "#94b8c8",
        "text_muted": "#5a8494",
    },
    "ember": {
        "label": "Закат",
        "accent": "#f97316",
        "accent_hover": "#fb923c",
        "bg_root": "#100a08",
        "bg_sidebar": "#18100c",
        "bg_panel": "#201612",
        "bg_card": "#281c18",
        "bg_input": "#30221c",
        "bg_hover": "#3a2a22",
        "bg_selected": "#443228",
        "border": "#503830",
        "border_light": "#604840",
        "text_primary": "#fff7ed",
        "text_secondary": "#c8a898",
        "text_muted": "#887068",
    },
    "forest": {
        "label": "Изумруд",
        "accent": "#10b981",
        "accent_hover": "#34d399",
        "bg_root": "#060e0a",
        "bg_sidebar": "#0a1410",
        "bg_panel": "#0e1a14",
        "bg_card": "#122018",
        "bg_input": "#16261c",
        "bg_hover": "#1c3024",
        "bg_selected": "#243a2c",
        "border": "#2c4a38",
        "border_light": "#3c6050",
        "text_primary": "#ecfdf5",
        "text_secondary": "#98c8b0",
        "text_muted": "#588870",
    },
    "graphite": {
        "label": "Графит",
        "accent": "#94a3b8",
        "accent_hover": "#cbd5e1",
        "bg_root": "#0c0c0e",
        "bg_sidebar": "#121214",
        "bg_panel": "#18181b",
        "bg_card": "#1f1f23",
        "bg_input": "#27272a",
        "bg_hover": "#2f2f35",
        "bg_selected": "#3a3a42",
        "border": "#3f3f46",
        "border_light": "#52525b",
        "text_primary": "#fafafa",
        "text_secondary": "#a1a1aa",
        "text_muted": "#71717a",
    },
    "rose": {
        "label": "Розовый кварц",
        "accent": "#ec4899",
        "accent_hover": "#f472b6",
        "bg_root": "#10080e",
        "bg_sidebar": "#180c16",
        "bg_panel": "#20121c",
        "bg_card": "#281824",
        "bg_input": "#301c2c",
        "bg_hover": "#3a2436",
        "bg_selected": "#442c40",
        "border": "#503648",
        "border_light": "#684858",
        "text_primary": "#fdf2f8",
        "text_secondary": "#c8a8b8",
        "text_muted": "#886878",
    },
    "amber": {
        "label": "Янтарь",
        "accent": "#f59e0b",
        "accent_hover": "#fbbf24",
        "bg_root": "#100c06",
        "bg_sidebar": "#18120a",
        "bg_panel": "#201a10",
        "bg_card": "#282218",
        "bg_input": "#302a1c",
        "bg_hover": "#3a3422",
        "bg_selected": "#443c28",
        "border": "#504830",
        "border_light": "#686040",
        "text_primary": "#fffbeb",
        "text_secondary": "#c8b898",
        "text_muted": "#887858",
    },
}

PRESET_IDS = list(PRESETS.keys())
PRESET_LABELS = [PRESETS[k]["label"] for k in PRESET_IDS]


def preset_id_by_label(label: str) -> str:
    for pid, p in PRESETS.items():
        if p["label"] == label:
            return pid
    return "helperp"


def resolve_palette(preset_id: str, custom_accent: str = "") -> dict:
    base = dict(PRESETS.get(preset_id) or PRESETS["helperp"])
    accent = (custom_accent or "").strip()
    if accent.startswith("#") and len(accent) in (4, 7):
        base["accent"] = accent
        base["accent_hover"] = _lighten_hex(accent, 0.15)
    return base


def _lighten_hex(color: str, amount: float) -> str:
    color = color.lstrip("#")
    if len(color) == 3:
        color = "".join(c * 2 for c in color)
    r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    return f"#{r:02x}{g:02x}{b:02x}"