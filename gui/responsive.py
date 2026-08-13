"""Адаптивный перенос текста при изменении размера окна."""

from __future__ import annotations

import customtkinter as ctk


class AdaptiveWrap:
    """Обновляет wraplength у CTkLabel при ресайзе контейнера."""

    def __init__(self, root: ctk.CTk):
        self._root = root
        self._items: list[tuple[ctk.CTkLabel, ctk.CTkBaseClass, int]] = []
        self._job = None

    def track(self, label: ctk.CTkLabel, container, padding: int = 32):
        self._items.append((label, container, padding))
        container.bind("<Configure>", lambda e: self.schedule(), add="+")
        self.schedule()

    def schedule(self):
        if self._job:
            self._root.after_cancel(self._job)
        self._job = self._root.after(60, self.refresh)

    def refresh(self):
        self._job = None
        for label, container, pad in self._items:
            try:
                if not label.winfo_exists():
                    continue
                w = container.winfo_width()
                if w > 40:
                    label.configure(wraplength=max(100, w - pad))
            except Exception:
                pass


def grid_flow_buttons(parent, buttons, columns: int = 3):
    """Кнопки/чипы в сетке с переносом строк (не в одну линию)."""
    for i, btn in enumerate(buttons):
        btn.grid(row=i // columns, column=i % columns, padx=3, pady=3, sticky="w")
