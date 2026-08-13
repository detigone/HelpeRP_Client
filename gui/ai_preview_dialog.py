"""Предпросмотр ИИ-отыгровки перед отправкой в чат."""

import customtkinter as ctk

from core.config import app_config
from gui import theme as T
from gui.icons import ui_icon


class AIPreviewDialog(ctk.CTkToplevel):
    def __init__(self, parent, lines: list[str], on_send, on_cancel=None):
        super().__init__(parent)
        self.on_send = on_send
        self.on_cancel = on_cancel
        self.lines = lines

        self.title("Предпросмотр отыгровки")
        self.configure(fg_color=T.BG_ROOT)
        self.geometry("520x420")
        self.transient(parent)
        self.grab_set()

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=T.PAD, pady=(T.PAD, T.PAD_SM))
        ic = ui_icon("ai", 24)
        if ic:
            ctk.CTkLabel(header, text="", image=ic).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            header, text="Проверьте строки перед отправкой",
            font=T.FONT_HEADING, text_color=T.TEXT_PRIMARY,
        ).pack(side="left")

        self.text = ctk.CTkTextbox(
            self, font=T.FONT_BODY, fg_color=T.BG_PANEL,
            border_width=1, border_color=T.BORDER, wrap="word",
        )
        self.text.pack(fill="both", expand=True, padx=T.PAD, pady=(0, T.PAD_SM))
        self.text.insert("0.0", "\n".join(lines))

        auto = app_config.get("ui", {}).get("auto_send_ai", False)
        self.auto_var = ctk.BooleanVar(value=auto)
        ctk.CTkCheckBox(
            self, text="Отправлять сразу без предпросмотра (запомнить)",
            variable=self.auto_var, font=T.FONT_TINY, text_color=T.TEXT_SECONDARY,
        ).pack(anchor="w", padx=T.PAD, pady=(0, T.PAD_SM))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=T.PAD, pady=(0, T.PAD))
        ctk.CTkButton(
            actions, text="Отмена", width=100, fg_color=T.BG_HOVER,
            hover_color=T.BORDER, command=self._cancel,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            actions, text="Отправить в чат", width=150,
            fg_color=T.DEFAULT_ACCENT, hover_color=T.DEFAULT_ACCENT_HOVER,
            command=self._confirm,
        ).pack(side="right")

    def _confirm(self):
        ui = app_config.get("ui", {})
        ui["auto_send_ai"] = bool(self.auto_var.get())
        app_config.set("ui", ui)
        text = self.text.get("0.0", "end").strip()
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        self.on_send(lines)
        self.destroy()

    def _cancel(self):
        if self.on_cancel:
            self.on_cancel()
        self.destroy()
