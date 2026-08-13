"""Диалог настроек HelpeRP."""

import customtkinter as ctk

from core.config import app_config
from gui import theme as T
from gui.icons import ui_icon


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_saved=None):
        super().__init__(parent)
        self.on_saved = on_saved
        self.title("Настройки HelpeRP")
        self.configure(fg_color=T.BG_ROOT)
        self.geometry("500x560")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        icon = ui_icon("settings", 24)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=T.PAD, pady=(T.PAD, T.PAD_SM))
        if icon:
            ctk.CTkLabel(header, text="", image=icon).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            header, text="Настройки", font=T.FONT_HEADING, text_color=T.TEXT_PRIMARY
        ).pack(side="left")

        scroll = ctk.CTkScrollableFrame(self, fg_color=T.BG_PANEL, corner_radius=T.RADIUS)
        scroll.pack(fill="both", expand=True, padx=T.PAD, pady=(0, T.PAD_SM))

        self._field(scroll, "API-ключ", "api_key", show="•")
        self._field(scroll, "Base URL (OpenAI-совместимый)", "base_url")
        self._field(scroll, "Модель ИИ", "model")

        c = app_config.get("character", {})
        self._entry(scroll, "Имя персонажа", "char_name", c.get("name", ""))
        self._entry(scroll, "Звание / должность", "char_rank", c.get("rank", ""))
        self._entry(scroll, "Жетон / №", "char_badge", c.get("badge", ""))
        self._textbox(scroll, "Характер и манера речи", "char_personality", c.get("personality", ""))

        game = app_config.get("game", {})
        self._entry(scroll, "Клавиша чата в игре (t, f6…)", "chat_key", game.get("chat_key", "t"))

        hk = app_config.get("hotkeys", {})
        self._entry(scroll, "Хоткей: компакт ↔ развёрнутый", "hotkey_toggle", hk.get("toggle_overlay", "shift+\\"))
        self._entry(scroll, "Хоткей: скрыть / показать окно", "hotkey_hide", hk.get("hide_window", "ctrl+shift+h"))

        ui = app_config.get("ui", {})
        self._entry(scroll, "Лимит записей в списке", "list_limit", str(ui.get("list_limit", 120)))
        self.auto_ai = ctk.BooleanVar(value=ui.get("auto_send_ai", False))
        ctk.CTkCheckBox(
            scroll, text="Отправлять ИИ-отыгровку сразу (без предпросмотра)",
            variable=self.auto_ai, font=T.FONT_TINY, text_color=T.TEXT_SECONDARY,
        ).pack(anchor="w", padx=T.PAD, pady=T.PAD_SM)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=T.PAD, pady=(0, T.PAD))
        ctk.CTkButton(
            actions, text="Отмена", width=100, fg_color=T.BG_HOVER,
            hover_color=T.BORDER, command=self.destroy,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            actions, text="Сохранить", width=120,
            fg_color=T.DEFAULT_ACCENT, hover_color=T.DEFAULT_ACCENT_HOVER,
            command=self._save,
        ).pack(side="right")

    def _field(self, parent, label, key, show=None):
        ctk.CTkLabel(
            parent, text=label, font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w",
        ).pack(fill="x", padx=T.PAD, pady=(T.PAD_SM, 2))
        entry = ctk.CTkEntry(
            parent, height=36, font=T.FONT_SMALL,
            fg_color=T.BG_INPUT, border_color=T.BORDER, show=show,
        )
        entry.pack(fill="x", padx=T.PAD, pady=(0, 4))
        entry.insert(0, str(app_config.get(key, "")))
        setattr(self, f"_{key}", entry)

    def _entry(self, parent, label, attr, value):
        ctk.CTkLabel(
            parent, text=label, font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w",
        ).pack(fill="x", padx=T.PAD, pady=(T.PAD_SM, 2))
        entry = ctk.CTkEntry(
            parent, height=36, font=T.FONT_SMALL,
            fg_color=T.BG_INPUT, border_color=T.BORDER,
        )
        entry.pack(fill="x", padx=T.PAD, pady=(0, 4))
        entry.insert(0, value)
        setattr(self, f"_{attr}", entry)

    def _textbox(self, parent, label, attr, value):
        ctk.CTkLabel(
            parent, text=label, font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w",
        ).pack(fill="x", padx=T.PAD, pady=(T.PAD_SM, 2))
        box = ctk.CTkTextbox(
            parent, height=70, font=T.FONT_SMALL,
            fg_color=T.BG_INPUT, border_color=T.BORDER,
        )
        box.pack(fill="x", padx=T.PAD, pady=(0, 4))
        box.insert("0.0", value)
        setattr(self, f"_{attr}", box)

    def _save(self):
        app_config.set("api_key", self._api_key.get().strip())
        app_config.set("base_url", self._base_url.get().strip())
        app_config.set("model", self._model.get().strip())
        app_config.set("character", {
            "name": self._char_name.get().strip(),
            "rank": self._char_rank.get().strip(),
            "badge": self._char_badge.get().strip(),
            "personality": self._char_personality.get("0.0", "end").strip(),
        })
        app_config.set("game", {"chat_key": self._chat_key.get().strip() or "t"})
        try:
            limit = max(40, min(500, int(self._list_limit.get().strip() or "120")))
        except ValueError:
            limit = 120
        app_config.set("ui", {
            "list_limit": limit,
            "auto_send_ai": bool(self.auto_ai.get()),
        })
        app_config.set("hotkeys", {
            "toggle_overlay": self._hotkey_toggle.get().strip() or "shift+\\",
            "hide_window": self._hotkey_hide.get().strip() or "ctrl+shift+h",
            "submit_request": app_config.get("hotkeys", {}).get("submit_request", "enter"),
        })
        if self.on_saved:
            self.on_saved()
        self.destroy()
