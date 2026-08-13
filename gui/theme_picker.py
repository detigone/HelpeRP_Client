"""Панель выбора темы оформления."""

from __future__ import annotations

import customtkinter as ctk

from core.config import app_config
from gui import theme as T
from gui.palettes import PRESET_IDS, PRESET_LABELS, PRESETS, preset_id_by_label, resolve_palette


class ThemePicker(ctk.CTkFrame):
    def __init__(self, master, accent: str = T.DEFAULT_ACCENT, on_preview=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.accent = accent
        self.on_preview = on_preview

        ui = app_config.get("ui", {}) or {}
        pid = ui.get("theme", "helperp")
        preset_label = PRESETS.get(pid, PRESETS["helperp"])["label"]

        ctk.CTkLabel(self, text="Тема оформления", font=T.FONT_TINY, text_color=T.TEXT_SECONDARY, anchor="w").pack(
            fill="x", pady=(T.PAD_SM, 2),
        )
        self.theme_box = ctk.CTkComboBox(
            self, values=PRESET_LABELS, height=36, font=T.FONT_SMALL,
            fg_color=T.BG_INPUT, border_color=T.BORDER, command=self._on_change,
        )
        self.theme_box.pack(fill="x")
        self.theme_box.set(preset_label if preset_label in PRESET_LABELS else PRESET_LABELS[0])

        ctk.CTkLabel(self, text="Свой акцент (#hex, необязательно)", font=T.FONT_TINY, text_color=T.TEXT_SECONDARY, anchor="w").pack(
            fill="x", pady=(T.PAD_SM, 2),
        )
        self.custom_accent = ctk.CTkEntry(
            self, height=34, font=T.FONT_SMALL, fg_color=T.BG_INPUT, border_color=T.BORDER,
            placeholder_text="#7c3aed",
        )
        self.custom_accent.pack(fill="x")
        self.custom_accent.insert(0, ui.get("custom_accent", ""))
        self.custom_accent.bind("<KeyRelease>", lambda e: self._on_change())

        self.use_faction_accent = ctk.BooleanVar(value=ui.get("use_faction_accent", True))
        ctk.CTkCheckBox(
            self, text="Акцент от выбранной фракции (иначе — из темы)",
            variable=self.use_faction_accent, font=T.FONT_SMALL, text_color=T.TEXT_SECONDARY,
            fg_color=accent, hover_color=T.DEFAULT_ACCENT_HOVER, command=self._on_change,
        ).pack(anchor="w", pady=(T.PAD_SM, 4))

        prev = ctk.CTkFrame(self, fg_color="transparent")
        prev.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(prev, text="Превью:", font=T.FONT_TINY, text_color=T.TEXT_MUTED).pack(side="left", padx=(0, 8))
        self.sw_bg = ctk.CTkFrame(prev, width=36, height=22, corner_radius=6, fg_color=T.BG_ROOT, border_width=1, border_color=T.BORDER)
        self.sw_bg.pack(side="left", padx=2)
        self.sw_card = ctk.CTkFrame(prev, width=36, height=22, corner_radius=6, fg_color=T.BG_CARD, border_width=1, border_color=T.BORDER)
        self.sw_card.pack(side="left", padx=2)
        self.sw_accent = ctk.CTkFrame(prev, width=36, height=22, corner_radius=6, fg_color=T.DEFAULT_ACCENT)
        self.sw_accent.pack(side="left", padx=2)

        self._update_swatches()

    def _on_change(self, *_):
        self._update_swatches()
        if self.on_preview:
            self.on_preview()

    def _update_swatches(self):
        pal = resolve_palette(self.get_preset_id(), self.custom_accent.get().strip())
        self.sw_bg.configure(fg_color=pal["bg_root"])
        self.sw_card.configure(fg_color=pal["bg_card"], border_color=pal["border"])
        self.sw_accent.configure(fg_color=pal["accent"])

    def get_preset_id(self) -> str:
        return preset_id_by_label(self.theme_box.get())

    def get_values(self) -> dict:
        return {
            "theme": self.get_preset_id(),
            "custom_accent": self.custom_accent.get().strip(),
            "use_faction_accent": bool(self.use_faction_accent.get()),
        }

    def reload(self):
        ui = app_config.get("ui", {}) or {}
        pid = ui.get("theme", "helperp")
        label = PRESETS.get(pid, PRESETS["helperp"])["label"]
        self.theme_box.set(label if label in PRESET_LABELS else PRESET_LABELS[0])
        self.custom_accent.delete(0, "end")
        self.custom_accent.insert(0, ui.get("custom_accent", ""))
        self.use_faction_accent.set(ui.get("use_faction_accent", True))
        self._update_swatches()

    def set_accent(self, color: str):
        self.accent = color
