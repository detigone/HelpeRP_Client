"""Просмотр лицензионного соглашения."""

import os

import customtkinter as ctk

from core.paths import legal_dir
from core.version import COPYRIGHT, EULA_VERSION, PRODUCT_NAME, VERSION
from gui import theme as T


def load_eula_text(lang: str = "ru") -> str:
    name = "EULA_RU.txt" if lang == "ru" else "EULA_EN.txt"
    path = os.path.join(legal_dir(), name)
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return f"EULA {PRODUCT_NAME} v{EULA_VERSION} — файл не найден."


class EulaDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title(f"{PRODUCT_NAME} — EULA")
        self.configure(fg_color=T.BG_ROOT)
        self.geometry("580x520")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=T.PAD, pady=(T.PAD, T.PAD_SM))
        ctk.CTkLabel(
            hdr, text=f"Лицензионное соглашение v{EULA_VERSION}",
            font=T.FONT_HEADING, text_color=T.TEXT_PRIMARY,
        ).pack(anchor="w")

        box = ctk.CTkTextbox(
            self, font=T.FONT_TINY, fg_color=T.BG_PANEL,
            border_width=1, border_color=T.BORDER, wrap="word",
        )
        box.pack(fill="both", expand=True, padx=T.PAD, pady=(0, T.PAD_SM))
        box.insert("0.0", load_eula_text())
        box.configure(state="disabled")

        ctk.CTkLabel(self, text=f"{PRODUCT_NAME} v{VERSION} · {COPYRIGHT}", font=T.FONT_TINY, text_color=T.TEXT_MUTED).pack(
            pady=(0, 4)
        )
        ctk.CTkButton(
            self, text="Закрыть", width=100, command=self.destroy,
            fg_color=T.BG_HOVER, hover_color=T.BORDER,
        ).pack(pady=(0, T.PAD))


def show_eula(parent):
    EulaDialog(parent)
