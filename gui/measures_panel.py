"""Раздел «Меры и наказания»."""

import customtkinter as ctk

from core.config import app_config
from core.measures import RP_LEVELS, load_measures, filter_measures
from gui import theme as T
from gui.responsive import AdaptiveWrap
from gui.toast import show_toast
from gui.animations import Animator, animations_enabled


class MeasuresPanel(ctk.CTkFrame):
    def __init__(self, master, accent: str = T.DEFAULT_ACCENT, adaptive: AdaptiveWrap | None = None, **kwargs):
        super().__init__(master, fg_color=T.BG_ROOT, **kwargs)
        self.accent = accent
        self._adaptive = adaptive
        self._all = load_measures()
        self._filtered: list = []
        self._selected = None
        self._selected_key = None
        self._kind = "all"
        self._level_filter = None
        self._limit = int(app_config.get("ui", {}).get("list_limit", 120))
        self._show_all = False
        self.list_buttons: dict = {}
        self._list_index = 0

        self.grid_columnconfigure(0, weight=1, minsize=260)
        self.grid_columnconfigure(1, weight=2, minsize=280)
        self.grid_rowconfigure(2, weight=1)

        self._build_toolbar()
        self._build_legend()
        self._build_list()
        self._build_detail()
        self._refresh()

    def set_accent(self, color: str):
        self.accent = color
        if hasattr(self, "det_title"):
            self.det_title.configure(text_color=color)

    def apply_theme(self, accent: str | None = None):
        if accent:
            self.accent = accent
        self.configure(fg_color=T.BG_ROOT)
        self.search.configure(fg_color=T.BG_INPUT, border_color=T.BORDER)
        self.level_box.configure(fg_color=T.BG_INPUT, border_color=T.BORDER)
        if hasattr(self, "_legend_panel"):
            self._legend_panel.configure(fg_color=T.BG_PANEL, border_color=T.BORDER)
        if hasattr(self, "_list_panel"):
            self._list_panel.configure(fg_color=T.BG_PANEL, border_color=T.BORDER)
        if hasattr(self, "detail_panel"):
            self.detail_panel.configure(fg_color=T.BG_PANEL, border_color=T.BORDER)
        if hasattr(self, "det_body"):
            self.det_body.configure(fg_color=T.BG_CARD, border_color=T.BORDER)
        if hasattr(self, "det_title"):
            self.det_title.configure(text_color=self.accent)
        self._refresh()

    def set_list_limit(self, limit: int):
        self._limit = max(40, min(500, limit))
        self._show_all = False
        self._refresh()

    def navigate_list(self, delta: int):
        if not self._filtered:
            return
        self._list_index = max(0, min(len(self._filtered) - 1, self._list_index + delta))
        self._show(self._filtered[self._list_index])

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=T.PAD, pady=(0, T.PAD_SM))
        toolbar.grid_columnconfigure(0, weight=1)

        self.search = ctk.CTkEntry(
            toolbar, placeholder_text="Статья, преступление, штраф, розыск…",
            height=38, font=T.FONT_BODY, fg_color=T.BG_INPUT, border_color=T.BORDER,
        )
        self.search.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.search.bind("<KeyRelease>", lambda e: self._refresh())

        filters = ctk.CTkFrame(toolbar, fg_color="transparent")
        filters.grid(row=1, column=0, columnspan=2, sticky="ew")
        filters.grid_columnconfigure(0, weight=1)

        self.kind_seg = ctk.CTkSegmentedButton(
            filters, values=["Все", "УК", "КоАП", "Частые"], font=T.FONT_TINY, command=self._on_kind,
        )
        self.kind_seg.grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.level_box = ctk.CTkComboBox(
            filters,
            values=["Любой уровень", "1 ур.", "2 ур.", "3 ур.", "4 ур.", "5 ур.", "6 ур."],
            width=130, height=38, font=T.FONT_TINY, fg_color=T.BG_INPUT,
            command=self._on_level,
        )
        self.level_box.grid(row=0, column=1, sticky="w")
        self.level_box.set("Любой уровень")

    def _build_legend(self):
        self._legend_panel = ctk.CTkFrame(self, fg_color=T.BG_PANEL, corner_radius=T.RADIUS, border_width=1, border_color=T.BORDER)
        self._legend_panel.grid(row=1, column=0, columnspan=2, sticky="ew", padx=T.PAD, pady=(0, T.PAD_SM))
        inner = ctk.CTkFrame(self._legend_panel, fg_color="transparent")
        inner.pack(fill="x", padx=T.PAD_SM, pady=T.PAD_SM)
        ctk.CTkLabel(inner, text="УРОВНИ РОЗЫСКА — нажмите для фильтра", font=T.FONT_TINY, text_color=self.accent).pack(anchor="w")
        chips = ctk.CTkFrame(inner, fg_color="transparent")
        chips.pack(fill="x", pady=(6, 0))
        chips.grid_columnconfigure(0, weight=1)
        chips.grid_columnconfigure(1, weight=1)
        chips.grid_columnconfigure(2, weight=1)
        for i, (lvl, name, _) in enumerate(RP_LEVELS):
            ctk.CTkButton(
                chips, text=f"{lvl}: {name}", height=26, font=T.FONT_TINY,
                fg_color=T.BG_CARD, hover_color=T.BG_HOVER, text_color=T.TEXT_SECONDARY,
                command=lambda l=int(lvl): self._filter_level(l),
            ).grid(row=i // 3, column=i % 3, padx=3, pady=3, sticky="ew")

    def _filter_level(self, level: int):
        self._level_filter = level
        self.level_box.set(f"{level} ур.")
        self._show_all = False
        self._refresh()

    def _item_key(self, m: dict) -> str:
        return f"{m.get('kind')}-{m.get('article')}"

    def _build_list(self):
        self._list_panel = ctk.CTkFrame(self, fg_color=T.BG_PANEL, corner_radius=T.RADIUS, border_width=1, border_color=T.BORDER)
        self._list_panel.grid(row=2, column=0, sticky="nsew", padx=(T.PAD, T.PAD_SM), pady=(0, T.PAD))
        self._list_panel.grid_rowconfigure(1, weight=1)
        self._list_panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self._list_panel, text="СТАТЬИ И МЕРЫ", font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w").grid(
            row=0, column=0, sticky="w", padx=T.PAD, pady=(T.PAD_SM, 4),
        )
        self.list_scroll = ctk.CTkScrollableFrame(self._list_panel, fg_color="transparent")
        self.list_scroll.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
        self.count_label = ctk.CTkLabel(self._list_panel, text="", font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w")
        self.count_label.grid(row=2, column=0, sticky="w", padx=T.PAD, pady=(0, T.PAD_SM))

    def _build_detail(self):
        self.detail_panel = ctk.CTkFrame(
            self, fg_color=T.BG_PANEL, corner_radius=T.RADIUS, border_width=1, border_color=T.BORDER,
        )
        self.detail_panel.grid(row=2, column=1, sticky="nsew", padx=(T.PAD_SM, T.PAD), pady=(0, T.PAD))
        self.detail_panel.grid_rowconfigure(2, weight=1)
        self.detail_panel.grid_columnconfigure(0, weight=1)

        self.det_title = ctk.CTkLabel(
            self.detail_panel, text="Выберите статью", font=("Segoe UI", 16, "bold"),
            text_color=self.accent, anchor="w", justify="left",
        )
        self.det_title.grid(row=0, column=0, sticky="ew", padx=T.PAD, pady=(T.PAD, 0))

        self.det_punishment = ctk.CTkLabel(
            self.detail_panel, text="", font=T.FONT_SMALL, text_color=T.SUCCESS,
            anchor="w", justify="left",
        )
        self.det_punishment.grid(row=1, column=0, sticky="ew", padx=T.PAD, pady=(8, 0))

        self.det_body = ctk.CTkTextbox(
            self.detail_panel, font=T.FONT_BODY, fg_color=T.BG_CARD, wrap="word",
            border_width=1, border_color=T.BORDER,
        )
        self.det_body.grid(row=2, column=0, sticky="nsew", padx=T.PAD, pady=T.PAD_SM)
        self.det_body.configure(state="disabled")

        self.det_hint = ctk.CTkLabel(
            self.detail_panel, text="", font=T.FONT_TINY, text_color=T.TEXT_MUTED,
            anchor="w", justify="left",
        )
        self.det_hint.grid(row=3, column=0, sticky="ew", padx=T.PAD, pady=(0, T.PAD_SM))

        if self._adaptive:
            pad = T.PAD * 2
            self._adaptive.track(self.det_title, self.detail_panel, padding=pad)
            self._adaptive.track(self.det_punishment, self.detail_panel, padding=pad)
            self._adaptive.track(self.det_hint, self.detail_panel, padding=pad)

        actions = ctk.CTkFrame(self.detail_panel, fg_color="transparent")
        actions.grid(row=4, column=0, sticky="ew", padx=T.PAD, pady=(0, T.PAD))
        ctk.CTkButton(
            actions, text="Копировать всё", width=130, height=34, font=T.FONT_SMALL,
            fg_color=T.BG_HOVER, hover_color=T.BORDER, command=self._copy_full,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            actions, text="Только меру", width=110, height=34, font=T.FONT_SMALL,
            fg_color=T.BG_HOVER, hover_color=T.BORDER, command=self._copy_measure,
        ).pack(side="left")

    def _on_kind(self, value):
        self._kind = {"Все": "all", "УК": "uk", "КоАП": "koap", "Частые": "frequent"}.get(value, "all")
        self._show_all = False
        self._refresh()

    def _on_level(self, value):
        self._level_filter = None if value == "Любой уровень" else int(value.split()[0])
        self._show_all = False
        self._refresh()

    def _refresh(self):
        self._filtered = filter_measures(
            self._all, query=self.search.get().strip(), kind=self._kind, level=self._level_filter,
        )
        self._list_index = 0
        self._render_list()

    def _highlight(self, key: str):
        for k, btn in self.list_buttons.items():
            if k == key:
                Animator.highlight_button(btn, self.winfo_toplevel(), self.accent)
            else:
                btn.configure(fg_color=T.BG_CARD, border_width=0)

    def _render_list(self):
        for w in self.list_scroll.winfo_children():
            w.destroy()
        self.list_buttons.clear()

        if not self._show_all and len(self._filtered) > self._limit:
            show, rest = self._filtered[: self._limit], len(self._filtered) - self._limit
        else:
            show, rest = self._filtered, 0

        self.count_label.configure(text=f"Показано {len(show)} из {len(self._filtered)}")

        if not show:
            ctk.CTkLabel(self.list_scroll, text="Нет статей по фильтру", font=T.FONT_BODY, text_color=T.TEXT_MUTED).pack(pady=40)
            return

        for m in show:
            key = self._item_key(m)
            lvl = m.get("level")
            lvl_txt = f" [{lvl} ур.]" if lvl else ""
            pun = m["punishment"][:39] + "…" if len(m["punishment"]) > 42 else m["punishment"]
            btn = ctk.CTkButton(
                self.list_scroll, text=f"ст. {m['article']}{lvl_txt}\n{pun}", anchor="w", height=52,
                font=T.FONT_TINY, fg_color=T.BG_CARD, hover_color=T.BG_HOVER,
                text_color=T.TEXT_PRIMARY, corner_radius=T.RADIUS_SM,
                command=lambda item=m, k=key: self._show(item, k),
            )
            btn.pack(fill="x", pady=2)
            self.list_buttons[key] = btn

        Animator.stagger_buttons(self.winfo_toplevel(), list(self.list_buttons.values()))

        if rest > 0:
            ctk.CTkButton(
                self.list_scroll, text=f"Ещё {rest}…", height=34, font=T.FONT_TINY,
                fg_color=T.BG_HOVER, command=self._show_more,
            ).pack(fill="x", pady=6)

        if show:
            idx = min(self._list_index, len(show) - 1)
            m = show[idx]
            self._show(m, self._item_key(m))

    def _show_more(self):
        self._show_all = True
        self._render_list()

    def _level_hint(self, level: int | None) -> str:
        if level is None:
            return ""
        for lvl, name, desc in RP_LEVELS:
            if lvl == str(level):
                return f"Уровень {level} ({name}): {desc}"
        return ""

    def _show(self, m: dict, key: str | None = None):
        self._selected = m
        self._selected_key = key or self._item_key(m)
        if m in self._filtered:
            self._list_index = self._filtered.index(m)
        self._highlight(self._selected_key)

        self.det_title.configure(text=f"ст. {m['article']} — {m['title']}")
        self.det_punishment.configure(text=f"▸ Мера: {m['punishment']}")

        body = m.get("description", "")
        if m.get("chapter"):
            body += f"\n\n▸ {m['chapter']}"
        if m.get("keywords"):
            body += f"\n\n▸ Ключевые слова: {', '.join(m['keywords'][:12])}"

        self.det_body.configure(state="normal")
        self.det_body.delete("0.0", "end")
        self.det_body.insert("0.0", body)
        self.det_body.configure(state="disabled")

        hint = self._level_hint(m.get("level"))
        if m["kind"] == "koap" and not hint:
            hint = "Административная ответственность: штраф, лишение прав или арест до 15 суток."
        self.det_hint.configure(text=hint)

        if self._adaptive:
            self._adaptive.schedule()

    def _copy_measure(self):
        if not self._selected:
            return
        m = self._selected
        text = f"ст. {m['article']} — {m['title']}\nМера: {m['punishment']}"
        self.winfo_toplevel().clipboard_clear()
        self.winfo_toplevel().clipboard_append(text)
        show_toast(self.winfo_toplevel(), "Мера скопирована", accent=self.accent)

    def _copy_full(self):
        if not self._selected:
            return
        m = self._selected
        text = f"ст. {m['article']} — {m['title']}\nМера: {m['punishment']}\n\n{m.get('description', '')}"
        self.winfo_toplevel().clipboard_clear()
        self.winfo_toplevel().clipboard_append(text.strip())
        show_toast(self.winfo_toplevel(), "Статья скопирована", accent=self.accent)
