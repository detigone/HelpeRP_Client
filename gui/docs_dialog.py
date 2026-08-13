"""Встроенная справка / документация HelpeRP."""

import os

import customtkinter as ctk

from core.paths import docs_dir
from core.version import PRODUCT_NAME, VERSION
from gui import theme as T
from gui.animations import ANIM_NORMAL, Animator, animations_enabled

DOC_FILES = [
    ("index", "О проекте"),
    ("user_guide", "Руководство пользователя"),
    ("install", "Установка"),
    ("updates", "Обновления"),
    ("faq", "FAQ"),
]


def _doc_path(key: str) -> str:
    return os.path.join(docs_dir(), f"{key}.md")


def load_doc(key: str) -> str:
    path = _doc_path(key)
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return f"Документ «{key}» не найден."


class DocsDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title(f"{PRODUCT_NAME} — документация")
        self.configure(fg_color=T.BG_ROOT)
        self.geometry("720x560")
        self.minsize(560, 420)
        self.transient(parent)

        if animations_enabled():
            try:
                self.attributes("-alpha", 0.0)
                self.after(30, lambda: Animator.fade_window(self, 0.0, 1.0, ANIM_NORMAL))
            except Exception:
                pass

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=T.PAD, pady=(T.PAD, T.PAD_SM))
        ctk.CTkLabel(hdr, text="Документация HelpeRP", font=T.FONT_HEADING, text_color=T.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(hdr, text=f"v{VERSION}", font=T.FONT_TINY, text_color=T.TEXT_MUTED).pack(side="right")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=T.PAD, pady=(0, T.PAD))
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        nav = ctk.CTkFrame(body, fg_color=T.BG_PANEL, corner_radius=T.RADIUS, width=200)
        nav.grid(row=0, column=0, sticky="nsew", padx=(0, T.PAD_SM))
        nav.grid_propagate(False)

        self._nav_inner = ctk.CTkScrollableFrame(nav, fg_color="transparent")
        self._nav_inner.pack(fill="both", expand=True, padx=6, pady=6)

        self.content = ctk.CTkTextbox(
            body, font=T.FONT_SMALL, fg_color=T.BG_PANEL, border_width=1, border_color=T.BORDER, wrap="word",
        )
        self.content.grid(row=0, column=1, sticky="nsew")

        for key, label in DOC_FILES:
            ctk.CTkButton(
                self._nav_inner, text=label, anchor="w", height=34, font=T.FONT_TINY,
                fg_color=T.BG_CARD, hover_color=T.BG_HOVER,
                command=lambda k=key: self._show(k),
            ).pack(fill="x", pady=2)

        self._show("index")

        ctk.CTkButton(
            self, text="Закрыть", width=100, command=self.destroy,
            fg_color=T.BG_HOVER, hover_color=T.BORDER,
        ).pack(pady=(0, T.PAD))

    def _show(self, key: str):
        self.content.configure(state="normal")
        self.content.delete("0.0", "end")
        self.content.insert("0.0", load_doc(key))
        self.content.configure(state="disabled")


def show_docs(parent):
    DocsDialog(parent)
