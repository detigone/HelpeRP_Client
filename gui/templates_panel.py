"""Раздел «Шаблоны» — готовые /me, /do без ИИ."""

import customtkinter as ctk

from core.config import app_config
from core.templates import filter_templates, template_to_text
from gui import theme as T
from gui.animations import Animator, animations_enabled
from gui.toast import show_toast


class TemplatesPanel(ctk.CTkFrame):
    FACTIONS = ["Все", "МВД", "СК", "СМП", "МЧС", "СМИ", "ФСБ", "Армия", "Криминал", "Общее"]

    def __init__(self, master, accent: str = T.DEFAULT_ACCENT, **kwargs):
        super().__init__(master, fg_color=T.BG_ROOT, **kwargs)
        self.accent = accent
        self._filtered: list = []
        self._selected = None
        self.list_buttons: dict = {}

        self.grid_columnconfigure(0, weight=1, minsize=260)
        self.grid_columnconfigure(1, weight=2, minsize=280)
        self.grid_rowconfigure(1, weight=1)

        self._build_toolbar()
        self._build_list()
        self._build_detail()
        self._refresh()

    def set_accent(self, color: str):
        self.accent = color
        if hasattr(self, "title_label"):
            self.title_label.configure(text_color=color)
        if hasattr(self, "btn_send"):
            self.btn_send.configure(fg_color=color, hover_color=T.DEFAULT_ACCENT_HOVER)

    def apply_theme(self, accent: str | None = None):
        if accent:
            self.accent = accent
        self.configure(fg_color=T.BG_ROOT)
        self.search.configure(fg_color=T.BG_INPUT, border_color=T.BORDER)
        self.faction_box.configure(fg_color=T.BG_INPUT, border_color=T.BORDER)
        if hasattr(self, "_list_panel"):
            self._list_panel.configure(fg_color=T.BG_PANEL, border_color=T.BORDER)
        if hasattr(self, "_detail_panel"):
            self._detail_panel.configure(fg_color=T.BG_PANEL, border_color=T.BORDER)
        if hasattr(self, "body"):
            self.body.configure(fg_color=T.BG_CARD, border_color=T.BORDER)
        if hasattr(self, "title_label"):
            self.title_label.configure(text_color=self.accent)
        if hasattr(self, "btn_send"):
            self.btn_send.configure(fg_color=self.accent, hover_color=T.DEFAULT_ACCENT_HOVER)
        self._refresh()

    def _build_toolbar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=T.PAD, pady=(0, T.PAD_SM))
        bar.grid_columnconfigure(0, weight=1)

        self.search = ctk.CTkEntry(
            bar, placeholder_text="Поиск шаблона…", height=38, font=T.FONT_BODY,
            fg_color=T.BG_INPUT, border_color=T.BORDER,
        )
        self.search.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.search.bind("<KeyRelease>", lambda e: self._refresh())

        row = ctk.CTkFrame(bar, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew")
        ctk.CTkLabel(row, text="Фракция:", font=T.FONT_TINY, text_color=T.TEXT_MUTED).pack(side="left", padx=(0, 8))
        self.faction_box = ctk.CTkComboBox(
            row, values=self.FACTIONS, width=160, height=36, font=T.FONT_TINY,
            fg_color=T.BG_INPUT, command=lambda v: self._refresh(),
        )
        self.faction_box.pack(side="left")
        self.faction_box.set("Все")

        self.count_label = ctk.CTkLabel(
            row, text="", font=T.FONT_TINY, text_color=T.TEXT_MUTED,
        )
        self.count_label.pack(side="right")

    def _build_list(self):
        self._list_panel = ctk.CTkFrame(self, fg_color=T.BG_PANEL, corner_radius=T.RADIUS, border_width=1, border_color=T.BORDER)
        self._list_panel.grid(row=1, column=0, sticky="nsew", padx=(T.PAD, T.PAD_SM), pady=(0, T.PAD))
        self._list_panel.grid_rowconfigure(0, weight=1)
        self._list_panel.grid_columnconfigure(0, weight=1)
        self.list_scroll = ctk.CTkScrollableFrame(self._list_panel, fg_color="transparent")
        self.list_scroll.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

    def _build_detail(self):
        self._detail_panel = ctk.CTkFrame(self, fg_color=T.BG_PANEL, corner_radius=T.RADIUS, border_width=1, border_color=T.BORDER)
        self._detail_panel.grid(row=1, column=1, sticky="nsew", padx=(T.PAD_SM, T.PAD), pady=(0, T.PAD))
        self._detail_panel.grid_rowconfigure(2, weight=1)
        self._detail_panel.grid_columnconfigure(0, weight=1)
        panel = self._detail_panel

        self.title_label = ctk.CTkLabel(
            panel, text="Выберите шаблон", font=("Segoe UI", 16, "bold"),
            text_color=self.accent, anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="ew", padx=T.PAD, pady=(T.PAD, 0))

        self.meta_label = ctk.CTkLabel(
            panel, text="Готовые команды /me и /do — без API-ключа",
            font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w",
        )
        self.meta_label.grid(row=1, column=0, sticky="ew", padx=T.PAD, pady=(4, 0))

        self.body = ctk.CTkTextbox(
            panel, font=T.FONT_BODY, fg_color=T.BG_CARD, wrap="word",
            border_width=1, border_color=T.BORDER,
        )
        self.body.grid(row=2, column=0, sticky="nsew", padx=T.PAD, pady=T.PAD_SM)
        self.body.configure(state="disabled")

        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=T.PAD, pady=(0, T.PAD))
        ctk.CTkButton(
            actions, text="Копировать", width=120, height=34, font=T.FONT_SMALL,
            fg_color=T.BG_HOVER, hover_color=T.BORDER, command=self._copy,
        ).pack(side="left", padx=(0, 8))
        self.btn_send = ctk.CTkButton(
            actions, text="Отправить в чат", width=140, height=34, font=T.FONT_SMALL,
            fg_color=self.accent, hover_color=T.DEFAULT_ACCENT_HOVER, command=self._send,
        )
        self.btn_send.pack(side="left")

    def _refresh(self):
        self._filtered = filter_templates(
            self.search.get().strip(),
            self.faction_box.get(),
        )
        self._render_list()
        if self._filtered:
            self._show(self._filtered[0])

    def _render_list(self):
        for w in self.list_scroll.winfo_children():
            w.destroy()
        self.list_buttons.clear()
        self.count_label.configure(text=f"{len(self._filtered)} шаблонов")

        if not self._filtered:
            ctk.CTkLabel(
                self.list_scroll, text="Шаблоны не найдены", font=T.FONT_BODY, text_color=T.TEXT_MUTED,
            ).pack(pady=40)
            return

        for t in self._filtered:
            tid = t.get("id", t.get("title", ""))
            sub = f"{t.get('faction', '')} · {t.get('category', '')}"
            btn = ctk.CTkButton(
                self.list_scroll,
                text=f"{t.get('title', '—')}\n{sub}",
                anchor="w", height=48, font=T.FONT_TINY,
                fg_color=T.BG_CARD, hover_color=T.BG_HOVER,
                command=lambda item=t: self._show(item),
            )
            btn.pack(fill="x", pady=2)
            self.list_buttons[tid] = btn

        Animator.stagger_buttons(self.winfo_toplevel(), list(self.list_buttons.values()))

    def _show(self, template: dict):
        self._selected = template
        tid = template.get("id", template.get("title", ""))
        for k, btn in self.list_buttons.items():
            if k == tid:
                Animator.highlight_button(btn, self.winfo_toplevel(), self.accent)
            else:
                btn.configure(fg_color=T.BG_CARD, border_width=0)

        self.title_label.configure(text=template.get("title", "—"))
        tags = ", ".join(template.get("tags", [])[:6])
        self.meta_label.configure(
            text=f"{template.get('faction', '')} · {template.get('category', '')}  ·  {tags}",
        )
        self.body.configure(state="normal")
        self.body.delete("0.0", "end")
        self.body.insert("0.0", template_to_text(template))
        self.body.configure(state="disabled")

        if animations_enabled():
            Animator.color_pulse(self.body, self.winfo_toplevel(), T.BORDER, self.accent, duration=180, cycles=1)

    def _copy(self):
        if not self._selected:
            return
        text = template_to_text(self._selected)
        root = self.winfo_toplevel()
        root.clipboard_clear()
        root.clipboard_append(text)
        show_toast(root, "Шаблон скопирован", accent=self.accent)

    def _send(self):
        if not self._selected:
            return
        from core.hotkeys import send_rp_sequence
        lines = [ln.strip() for ln in template_to_text(self._selected).splitlines() if ln.strip()]
        send_rp_sequence(lines)
        show_toast(self.winfo_toplevel(), "Шаблон отправлен в чат", accent=self.accent)
