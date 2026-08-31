# HelpeRP_Client/gui/main_window.py
import customtkinter as ctk
import threading
from pathlib import Path

from core.config import app_config, effective_api_key
from core.factions import FACTIONS, load_faction_items, get_faction
from core.measures import load_measures
from core.paths import icons_dir
from core.search import filter_and_rank, item_blob
from gui import theme as T
from gui.ai_preview_dialog import AIPreviewDialog
from gui.icons import faction_icon, ui_icon, preload, nav_emoji, faction_emoji
from gui.measures_panel import MeasuresPanel
from gui.settings_panel import SettingsPanel
from gui.templates_panel import TemplatesPanel
from gui.toast import show_toast
from gui.responsive import AdaptiveWrap
from gui.docs_dialog import show_docs
from gui.update_dialog import show_update_dialog
from gui.animations import (
    Animator, LoadingDots, PulseBadge, animations_enabled,
)


class HelpeRPMainWindow:
    def __init__(self):
        # Применить тему ДО создания виджетов
        from gui.theme_engine import load_theme_from_config
        load_theme_from_config()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self._icon_refs: list = []
        # Не делаем полный preload здесь — загрузим иконки лениво
        self._preload_basic_icons()

        self.root = ctk.CTk()
        self.root.title("HelpeRP — База знаний RP")
        self.root.configure(fg_color=T.BG_ROOT)
        self.root.attributes("-topmost", False)
        self.root.bind("<FocusIn>", lambda _e: self._set_topmost(True))
        self.root.bind("<FocusOut>", lambda _e: self._set_topmost(False))
        self._set_window_icon()

        self.is_expanded = True
        self.saved_geometry = None
        self.all_items = []
        self.filtered_items = []
        self.current_item = None
        self.current_faction = get_faction(
            app_config.get("current_faction", FACTIONS[0]["name"])
        )
        from gui.theme_engine import effective_accent
        self.accent, self._accent_hover = effective_accent(self.current_faction["accent"])
        self.is_hidden = False
        self.list_show_all = False
        self._list_index = 0
        self._settings_saved_callback = None
        self._pending_update = None
        self._detail_loader = None
        self._filter_after = None  # debounce для быстрого набора
        self._active_filters = {}  # тип фильтра -> значение
        self._chip_buttons = {}  # ключ чипа -> кнопка
        self._chips_container = None
        self._badge_pulse = None
        self.favorites_overlay = None
        self.current_page = "database"
        self.nav_buttons = {}
        self.faction_buttons = {}
        self.list_buttons = {}
        self.selected_list_key = None
        ui_cfg = app_config.get("ui", {})
        self.list_limit = int(ui_cfg.get("list_limit", 120))

        # Ленивые страницы (создаются при первом переключении)
        self._page_measures = None
        self._page_templates = None
        self._page_settings = None

        self._center_geometry(*T.EXPANDED_SIZE)
        self.root.minsize(960, 600)

        self._adaptive = AdaptiveWrap(self.root)
        
        # Создаем минимальный UI сразу
        self._build_ui_minimal()
        
        # Загружаем данные в фоне
        self._load_data_async()
        
        self._bind_keyboard_shortcuts()
        self._bind_resize()
        
        # Отложенные инициализации
        self.root.after(100, self._post_init)
        self.root.after(2000, lambda: self._run_update_check(force=False))
        self._schedule_update_checks()
        if animations_enabled():
            try:
                self.root.attributes("-alpha", 0.98)
                self.root.after(40, lambda: self.root.attributes("-alpha", 1.0))
            except Exception:
                pass

    def _set_topmost(self, active: bool):
        try:
            self.root.attributes("-topmost", bool(active))
        except Exception:
            pass
        if hasattr(self, "favorites_overlay") and self.favorites_overlay is not None and self.favorites_overlay.winfo_exists():
            try:
                self.favorites_overlay.attributes("-topmost", bool(active))
            except Exception:
                pass

    def _keep_icon(self, icon):
        if icon is not None:
            self._icon_refs.append(icon)
        return icon

    def _set_window_icon(self):
        icon_path = Path(icons_dir()) / "logo.png"
        if not icon_path.is_file():
            icon_path = Path(icons_dir()) / "diamond.png"
        if not icon_path.is_file():
            return
        try:
            from PIL import Image, ImageTk
            pil = Image.open(icon_path).convert("RGBA")
            photo = ImageTk.PhotoImage(pil)
            self.root.iconphoto(True, photo)
            self._icon_refs.append(photo)
        except Exception as e:
            print(f"[HelpeRP] Не удалось установить иконку окна: {e}")

    def _center_geometry(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        if h <= 60:
            x = (sw - w) // 2
            y = 12
        else:
            x = (sw - w) // 2
            y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _preload_basic_icons(self):
        """Предзагрузить только критичные иконки для старта."""
        from gui.icons import get_icon
        # Только лого и базовые UI иконки
        for name in ("logo.png", "home.png", "settings.png", "rules.png", "bolt.png"):
            get_icon(name, 22)
            get_icon(name, 28)

    def _build_ui_minimal(self):
        """Создать минимальный каркас UI без тяжелых страниц."""
        self.compact_frame = ctk.CTkFrame(
            self.root,
            fg_color=T.BG_SIDEBAR,
            corner_radius=T.RADIUS,
            border_width=1,
            border_color=T.BORDER,
        )
        self._build_compact()

        self.expanded_frame = ctk.CTkFrame(self.root, fg_color=T.BG_ROOT, corner_radius=0)
        self.expanded_frame.pack(fill="both", expand=True)
        self.expanded_frame.grid_columnconfigure(1, weight=1)
        self.expanded_frame.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main_minimal()

    def _build_main_minimal(self):
        """Создать только базовый main фрейм и database страницу."""
        self.main = ctk.CTkFrame(self.expanded_frame, fg_color=T.BG_ROOT, corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_columnconfigure(1, weight=2)
        self.main.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(self.main, fg_color="transparent")
        top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=T.PAD, pady=(T.PAD, 4))

        header_left = ctk.CTkFrame(top, fg_color="transparent")
        header_left.pack(side="left", fill="x", expand=True)

        title_row = ctk.CTkFrame(header_left, fg_color="transparent")
        title_row.pack(anchor="w")

        self.header_faction_icon = ctk.CTkLabel(title_row, text="", width=T.ICON_LG)
        self.header_faction_icon.pack(side="left", padx=(0, 8))

        self.faction_title = ctk.CTkLabel(
            title_row,
            text=self.current_faction["name"],
            font=T.FONT_HEADING,
            text_color=T.TEXT_PRIMARY,
            anchor="w",
        )
        self.faction_title.pack(side="left")
        self._header_left = header_left
        self._update_header_faction_icon()
        self._adaptive.track(self.faction_title, header_left, padding=48)

        collapse_icon = self._keep_icon(ui_icon("collapse", T.ICON_SM))
        self.btn_collapse = ctk.CTkButton(
            top,
            text="Свернуть",
            image=collapse_icon,
            compound="left",
            width=110,
            height=28,
            font=T.FONT_TINY,
            fg_color=T.BG_HOVER,
            hover_color=T.BORDER,
            command=lambda: self._set_mode(False),
        )
        self.btn_collapse.pack(side="right", padx=(8, 0))

        self.stats_label = ctk.CTkLabel(
            top, text="Загрузка…", font=T.FONT_SMALL, text_color=T.TEXT_SECONDARY
        )
        self.stats_label.pack(side="right")

        self.faction_sub = ctk.CTkLabel(
            self.main,
            text=self.current_faction.get("subtitle", ""),
            font=T.FONT_TINY,
            text_color=T.TEXT_MUTED,
            anchor="w",
            justify="left",
        )
        self.faction_sub.grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=T.PAD, pady=(0, T.PAD_SM)
        )
        self._adaptive.track(self.faction_sub, self.main, padding=T.PAD * 2)

        # Контейнер страниц
        self.pages = ctk.CTkFrame(self.main, fg_color="transparent")
        self.pages.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.pages.grid_columnconfigure(0, weight=1)
        self.pages.grid_rowconfigure(0, weight=1)

        # Создаем только database страницу сразу
        self.page_database = ctk.CTkFrame(self.pages, fg_color="transparent")
        self.page_database.grid(row=0, column=0, sticky="nsew")
        self.page_database.grid_columnconfigure(0, weight=1, minsize=260)
        self.page_database.grid_columnconfigure(1, weight=2, minsize=280)
        self.page_database.grid_rowconfigure(1, weight=1)

        self._build_database_page()
        
        # Страницы measures, templates, settings будут созданы лениво
        self.current_page = "database"
        self.page_database.grid()
        self._update_page_header()
        self.status_bar.grid()

    def _load_data_async(self):
        """Загрузить данные фракции и построить RAG индекс в фоне."""
        def worker():
            try:
                items, faction = load_faction_items(self.current_faction["name"])
                self.root.after(0, lambda: self._on_data_loaded(items, faction))
            except Exception as e:
                print(f"[Data] Ошибка загрузки: {e}")
                self.root.after(0, lambda: self._on_data_loaded([], self.current_faction))

        threading.Thread(target=worker, daemon=True, name="data-loader").start()

    def _on_data_loaded(self, items, faction):
        """Callback когда данные загружены."""
        # Очистить кэш поиска при смене данных
        from core.search import clear_blob_cache
        clear_blob_cache()
        
        self.all_items = items
        self.current_faction = faction
        self.filtered_items = list(self.all_items)
        
        # Обновить UI
        self._update_categories()
        self._refresh_list()
        self.stats_label.configure(text=self._stats_text())
        self._update_compact_bar()
        self._update_header_faction_icon()
        self.faction_title.configure(text=faction["name"])
        self.faction_sub.configure(text=faction.get("subtitle", ""))
        
        # Построить RAG индекс в фоне
        self._build_rag_index_async()
        
        # Обновить кнопки фракций
        for name, btn in self.faction_buttons.items():
            fac = get_faction(name)
            selected = name == faction["name"]
            btn.configure(
                fg_color=T.BG_SELECTED if selected else T.BG_CARD,
                border_width=2 if selected else 0,
                border_color=fac["accent"] if selected else T.BORDER,
            )

    def _build_rag_index_async(self):
        """Построить BM25 индекс в фоне."""
        def worker():
            try:
                from core.rag_search import ensure_rag_index
                ensure_rag_index(self.all_items)
            except Exception:
                pass
        
        threading.Thread(target=worker, daemon=True, name="rag-index").start()

    def _post_init(self):
        """Отложенная инициализация после показа окна."""
        self._adaptive.refresh()
        # Подгрузить остальные иконки в фоне
        self._preload_remaining_icons()

    def _preload_remaining_icons(self):
        """Подгрузить оставшиеся иконки в фоне."""
        def worker():
            from gui.icons import preload
            preload()
        threading.Thread(target=worker, daemon=True, name="icon-preload").start()

    def _load_data(self):
        """Deprecated: оставлен для совместимости."""
        pass

    def _refresh_character_box(self):
        from core.characters import character_labels, get_active_character
        labels = character_labels() or ["Основной"]
        self.character_box.configure(values=labels)
        active = get_active_character()
        label = active.get("label") or active.get("name") or labels[0]
        if label in labels:
            self.character_box.set(label)

    def _on_character_changed(self, label: str):
        from core.characters import character_id_by_label, set_active_character
        cid = character_id_by_label(label)
        if cid and set_active_character(cid):
            show_toast(self.root, f"Персонаж: {label}", accent=self.accent)

    def _build_ui(self):
        self.compact_frame = ctk.CTkFrame(
            self.root,
            fg_color=T.BG_SIDEBAR,
            corner_radius=T.RADIUS,
            border_width=1,
            border_color=T.BORDER,
        )
        self._build_compact()

        self.expanded_frame = ctk.CTkFrame(self.root, fg_color=T.BG_ROOT, corner_radius=0)
        self.expanded_frame.pack(fill="both", expand=True)
        self.expanded_frame.grid_columnconfigure(1, weight=1)
        self.expanded_frame.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main()

    def _build_compact(self):
        inner = ctk.CTkFrame(self.compact_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10, pady=8)

        self.compact_accent = ctk.CTkFrame(
            inner, width=4, fg_color=self.accent, corner_radius=2
        )
        self.compact_accent.pack(side="left", fill="y", padx=(0, 10))

        self.compact_faction_icon = ctk.CTkLabel(inner, text="", width=T.ICON_MD)
        self.compact_faction_icon.pack(side="left", padx=(0, 6))
        self._update_compact_faction_icon()

        self.compact_search = ctk.CTkEntry(
            inner,
            placeholder_text="Быстрый поиск…",
            height=32,
            font=T.FONT_SMALL,
            fg_color=T.BG_INPUT,
            border_color=T.BORDER,
            width=220,
        )
        self.compact_search.pack(side="left", padx=(0, 8))
        self.compact_search.bind("<KeyRelease>", self._on_compact_search)
        self.compact_search.bind("<Return>", lambda e: self._set_mode(True))

        self.compact_preview = ctk.CTkLabel(
            inner,
            text="",
            font=T.FONT_TINY,
            text_color=T.TEXT_MUTED,
            anchor="w",
        )
        self.compact_preview.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.compact_stats = ctk.CTkLabel(
            inner, text="", font=T.FONT_TINY, text_color=T.TEXT_MUTED, width=80
        )
        self.compact_stats.pack(side="right", padx=(0, 6))

        expand_icon = self._keep_icon(ui_icon("expand", T.ICON_MD))
        self.btn_expand = ctk.CTkButton(
            inner,
            text="",
            image=expand_icon,
            width=36,
            height=32,
            command=lambda: self._set_mode(True),
        )
        self.btn_expand.pack(side="right")
        self._update_compact_bar()

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self.expanded_frame, width=240, fg_color=T.BG_SIDEBAR, corner_radius=0
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        sidebar = self.sidebar

        header = ctk.CTkFrame(sidebar, fg_color="transparent")
        header.pack(fill="x", padx=T.PAD, pady=(T.PAD, T.PAD_SM))

        logo_row = ctk.CTkFrame(header, fg_color="transparent")
        logo_row.pack(fill="x", anchor="w")

        logo_icon = self._keep_icon(ui_icon("app", T.ICON_LG))
        if logo_icon:
            ctk.CTkLabel(logo_row, text="", image=logo_icon).pack(side="left", padx=(0, 8))

        title_col = ctk.CTkFrame(logo_row, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            title_col,
            text="HelpeRP",
            font=T.FONT_TITLE,
            text_color=T.TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_col,
            text="База знаний для RP",
            font=T.FONT_TINY,
            text_color=T.TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        self.accent_bar = ctk.CTkFrame(
            header, height=3, fg_color=self.accent, corner_radius=2
        )
        self.accent_bar.pack(fill="x", pady=(T.PAD_SM, 0))

        char_row = ctk.CTkFrame(header, fg_color="transparent")
        char_row.pack(fill="x", pady=(T.PAD_SM, 0))
        ctk.CTkLabel(char_row, text="Персонаж", font=T.FONT_TINY, text_color=T.TEXT_MUTED).pack(anchor="w")
        from core.characters import character_labels, get_active_character, set_active_character, character_id_by_label
        self._char_id_by_label = character_id_by_label
        labels = character_labels() or ["Основной"]
        self.character_box = ctk.CTkComboBox(
            char_row, values=labels, height=32, font=T.FONT_TINY, fg_color=T.BG_INPUT,
            command=self._on_character_changed,
        )
        self.character_box.pack(fill="x", pady=(4, 0))
        active = get_active_character()
        self.character_box.set(active.get("label") or active.get("name") or labels[0])

        ctk.CTkLabel(
            sidebar, text="РАЗДЕЛЫ", font=T.FONT_TINY, text_color=T.TEXT_MUTED
        ).pack(anchor="w", padx=T.PAD, pady=(T.PAD_SM, 4))

        nav = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav.pack(fill="x", padx=8, pady=(0, T.PAD_SM))

        for page_id, label, icon_key in (
            ("database", "База знаний", "home"),
            ("measures", "Меры", "rules"),
            ("templates", "Шаблоны", "bolt"),
            ("settings", "Настройки", "settings"),
        ):
            emoji = nav_emoji(page_id)
            selected = page_id == self.current_page
            btn = ctk.CTkButton(
                nav,
                text=f"{emoji}  {label}",
                anchor="w",
                height=36,
                font=T.FONT_SMALL,
                fg_color=T.BG_SELECTED if selected else T.BG_CARD,
                hover_color=T.BG_HOVER,
                text_color=T.TEXT_PRIMARY,
                corner_radius=T.RADIUS_SM,
                border_width=2 if selected else 0,
                border_color=self.accent if selected else T.BORDER,
                command=lambda p=page_id: self._switch_page(p),
            )
            btn.pack(fill="x", pady=2, padx=4)
            self.nav_buttons[page_id] = btn

        ctk.CTkLabel(
            sidebar, text="НЕДАВНИЕ", font=T.FONT_TINY, text_color=T.TEXT_MUTED
        ).pack(anchor="w", padx=T.PAD, pady=(T.PAD_SM, 2))

        self.recent_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        self.recent_frame.pack(fill="x", padx=8, pady=(0, T.PAD_SM))
        self._refresh_recent_sidebar()

        ctk.CTkLabel(
            sidebar, text="ФРАКЦИИ", font=T.FONT_TINY, text_color=T.TEXT_MUTED
        ).pack(anchor="w", padx=T.PAD, pady=(T.PAD_SM, 4))

        scroll = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        saved = app_config.get("current_faction", FACTIONS[0]["name"])
        for fac in FACTIONS:
            emoji = faction_emoji(fac["id"])
            selected = fac["name"] == saved
            btn = ctk.CTkButton(
                scroll,
                text=f"{emoji}  {fac['name']}",
                anchor="w",
                height=38,
                font=T.FONT_SMALL,
                fg_color=T.BG_SELECTED if selected else T.BG_CARD,
                hover_color=T.BG_HOVER,
                text_color=T.TEXT_PRIMARY,
                corner_radius=T.RADIUS_SM,
                border_width=2 if selected else 0,
                border_color=fac["accent"] if selected else T.BORDER,
                command=lambda f=fac: self._select_faction(f),
            )
            btn.pack(fill="x", pady=2, padx=4)
            self.faction_buttons[fac["name"]] = btn

        hotkey = app_config.get("hotkeys", {}).get("toggle_overlay", "shift+\\")
        hide_hk = app_config.get("hotkeys", {}).get("hide_window", "ctrl+shift+h")
        self._sidebar_footer = ctk.CTkFrame(sidebar, fg_color=T.BG_CARD, corner_radius=T.RADIUS_SM)
        self._sidebar_footer.pack(fill="x", padx=T.PAD, pady=(0, T.PAD))
        footer = self._sidebar_footer

        hints = ctk.CTkFrame(footer, fg_color="transparent")
        hints.pack(fill="x", padx=T.PAD_SM, pady=(T.PAD_SM, 4))
        self.hotkey_label = ctk.CTkLabel(
            hints, text=f"{hotkey.upper()} — режим",
            font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w",
        )
        self.hotkey_label.pack(anchor="w")
        self.hide_hotkey_label = ctk.CTkLabel(
            hints, text=f"{hide_hk.upper()} — скрыть окно",
            font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w",
        )
        self.hide_hotkey_label.pack(anchor="w")

        from core.version import COPYRIGHT, VERSION

        ver_row = ctk.CTkFrame(footer, fg_color="transparent")
        ver_row.pack(fill="x", padx=T.PAD_SM, pady=(0, 2))
        ctk.CTkLabel(
            ver_row, text=f"v{VERSION}", font=T.FONT_TINY, text_color=T.TEXT_MUTED,
        ).pack(side="left")
        self.update_badge = ctk.CTkButton(
            ver_row, text="", height=22, font=T.FONT_TINY, fg_color=T.BG_HOVER,
            hover_color=T.BORDER, text_color=T.WARNING, command=lambda: self._run_update_check(force=True),
        )
        self.update_badge.pack(side="left", padx=(8, 0))
        self.update_badge.pack_forget()
        self._badge_pulse = PulseBadge(self.update_badge, self.root, T.WARNING)
        self.footer_copy = ctk.CTkLabel(
            footer, text=COPYRIGHT, font=("Segoe UI", 8), text_color=T.TEXT_MUTED, justify="left",
        )
        self.footer_copy.pack(anchor="w", padx=T.PAD_SM, pady=(0, 4))
        self._adaptive.track(self.footer_copy, sidebar, padding=24)

        footer_inner = ctk.CTkFrame(footer, fg_color="transparent")
        footer_inner.pack(fill="x", padx=T.PAD_SM, pady=(0, T.PAD_SM))

        settings_icon = self._keep_icon(ui_icon("settings", T.ICON_SM))
        settings_btn = ctk.CTkButton(
            footer_inner,
            text="  Настройки",
            image=settings_icon,
            compound="left",
            height=34,
            font=T.FONT_TINY,
            fg_color=T.BG_HOVER,
            hover_color=T.BORDER,
            corner_radius=T.RADIUS_SM,
            border_width=1,
            border_color=T.BORDER,
            command=lambda: self._switch_page("settings"),
        )
        settings_btn.pack(fill="x", pady=(0, 4))

        docs_icon = self._keep_icon(ui_icon("info", T.ICON_SM))
        docs_btn = ctk.CTkButton(
            footer_inner,
            text="  Справка",
            image=docs_icon,
            compound="left",
            height=34,
            font=T.FONT_TINY,
            fg_color=T.BG_HOVER,
            hover_color=T.BORDER,
            corner_radius=T.RADIUS_SM,
            border_width=1,
            border_color=T.BORDER,
            command=lambda: show_docs(self.root),
        )
        docs_btn.pack(fill="x")

    def _refresh_recent_sidebar(self):
        for w in self.recent_frame.winfo_children():
            w.destroy()
        recent = app_config.get("recent", [])[:6]
        if not recent:
            ctk.CTkLabel(
                self.recent_frame, text="Пока пусто", font=T.FONT_TINY, text_color=T.TEXT_MUTED,
            ).pack(anchor="w", padx=4)
            return
        for rec in recent:
            title = rec.get("title", "—")
            short = title if len(title) <= 28 else title[:25] + "…"
            ctk.CTkButton(
                self.recent_frame, text=short, anchor="w", height=28, font=T.FONT_TINY,
                fg_color=T.BG_CARD, hover_color=T.BG_HOVER, text_color=T.TEXT_SECONDARY,
                corner_radius=T.RADIUS_SM,
                command=lambda r=rec: self._open_recent(r),
            ).pack(fill="x", pady=1, padx=4)

    def _open_recent(self, rec: dict):
        self._switch_page("database")
        fac_name = rec.get("faction", self.current_faction["name"])
        fac = get_faction(fac_name)
        if fac["name"] != self.current_faction["name"]:
            self._select_faction(fac)
        key = rec.get("key")
        for item in self.all_items:
            if self._item_key(item) == key:
                self._show_item(item, key)
                return
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, rec.get("title", ""))
        self._on_filter()

    def _switch_page(self, page: str):
        if page == self.current_page and page != "settings":
            return

        leaving_settings = self.current_page == "settings" and page != "settings"

        # Ленивая инициализация страниц
        if page == "measures" and self._page_measures is None:
            self._page_measures = MeasuresPanel(self.pages, accent=self.accent, adaptive=self._adaptive)
            self._page_measures.grid(row=0, column=0, sticky="nsew")
            self._page_measures.grid_remove()
        elif page == "templates" and self._page_templates is None:
            self._page_templates = TemplatesPanel(self.pages, accent=self.accent)
            self._page_templates.grid(row=0, column=0, sticky="nsew")
            self._page_templates.grid_remove()
        elif page == "settings" and self._page_settings is None:
            self._page_settings = SettingsPanel(
                self.pages,
                on_saved=self._on_settings_saved,
                on_check_updates=self._run_update_check,
                on_theme_preview=self._preview_theme,
                accent=self.accent,
            )
            self._page_settings.grid(row=0, column=0, sticky="nsew")
            self._page_settings.grid_remove()

        def apply():
            if leaving_settings:
                app_config.load_config()
                from gui.theme_engine import load_theme_from_config
                load_theme_from_config()
                self.apply_visual_theme()

            self.current_page = page
            pages = {
                "database": self.page_database,
                "measures": self._page_measures,
                "templates": self._page_templates,
                "settings": self._page_settings,
            }
            for name, frame in pages.items():
                if frame is None:
                    continue
                if name == page:
                    frame.grid()
                else:
                    frame.grid_remove()

            for name, btn in self.nav_buttons.items():
                selected = name == page
                btn.configure(
                    fg_color=T.BG_SELECTED if selected else T.BG_CARD,
                    border_width=2 if selected else 0,
                    border_color=self.accent if selected else T.BORDER,
                )

            self._update_page_header()

            if page == "settings":
                if self._page_settings:
                    self._page_settings.reload_from_config()
            elif page == "database":
                self.status_bar.grid()
            else:
                self.status_bar.grid_remove()

            if animations_enabled():
                Animator.flash_bar(self.accent_bar, self.root, self.accent)

        if animations_enabled() and hasattr(self, "pages") and page != "database":
            def nudge(t, _):
                pad = int(10 * (1 - abs(t * 2 - 1)))
                self.pages.grid_configure(padx=pad)

            Animator.tween(self.root, 120, nudge, on_done=apply)
        else:
            apply()

    def _update_page_header(self):
        page = self.current_page
        if page == "database":
            self._update_header_faction_icon()
            self.faction_title.configure(text=self.current_faction["name"])
            self.faction_sub.configure(text=self.current_faction.get("subtitle", ""))
            self.stats_label.configure(text=self._stats_text())
            if self.stats_label.winfo_ismapped():
                pass
            else:
                self.stats_label.pack(side="right")
            self.faction_sub.grid()
        elif page == "measures":
            rules_icon = self._keep_icon(ui_icon("rules", T.ICON_LG))
            if rules_icon:
                self.header_faction_icon.configure(image=rules_icon)
            self.faction_title.configure(text="Меры и наказания")
            # Ленивая загрузка количества мер
            if not hasattr(self, "_measures_count"):
                def load_count():
                    try:
                        from core.measures import load_measures
                        count = len(load_measures())
                        self.root.after(0, lambda: self._set_measures_count(count))
                    except Exception:
                        pass
                threading.Thread(target=load_count, daemon=True).start()
                self._measures_count = "…"
            self.faction_sub.configure(
                text=f"Справочник из законодательства · {self._measures_count} статей"
            )
            if self.stats_label.winfo_ismapped():
                self.stats_label.pack_forget()
            self.faction_sub.grid()
        elif page == "templates":
            tpl_icon = self._keep_icon(ui_icon("bolt", T.ICON_LG))
            if tpl_icon:
                self.header_faction_icon.configure(image=tpl_icon)
            self.faction_title.configure(text="Шаблоны отыгровок")
            self.faction_sub.configure(text="Готовые /me и /do — без ИИ и API-ключа")
            if self.stats_label.winfo_ismapped():
                self.stats_label.pack_forget()
            self.faction_sub.grid()
        else:
            settings_icon = self._keep_icon(ui_icon("settings", T.ICON_LG))
            if settings_icon:
                self.header_faction_icon.configure(image=settings_icon)
            self.faction_title.configure(text="Настройки HelpeRP")
            self.faction_sub.configure(text="ИИ, персонаж, хоткеи, интерфейс")
            if self.stats_label.winfo_ismapped():
                self.stats_label.pack_forget()
            self.faction_sub.grid()

    def _set_measures_count(self, count):
        self._measures_count = count
        if self.current_page == "measures":
            self.faction_sub.configure(
                text=f"Справочник из законодательства · {count} статей"
            )

    

    def _build_database_page(self):
        db = self.page_database

        toolbar = ctk.CTkFrame(db, fg_color="transparent")
        toolbar.grid(
            row=0, column=0, columnspan=2, sticky="ew", padx=T.PAD, pady=(0, T.PAD_SM)
        )
        toolbar.grid_columnconfigure(0, weight=1)
        toolbar.grid_columnconfigure(1, weight=0)

        search_wrap = ctk.CTkFrame(toolbar, fg_color="transparent")
        search_wrap.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        search_wrap.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            search_wrap,
            placeholder_text="Поиск: название, статья, ключевые слова…",
            height=40,
            font=T.FONT_BODY,
            fg_color=T.BG_INPUT,
            border_color=T.BORDER,
        )
        self.search_entry.grid(row=0, column=0, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self._on_search_typed)

        self.btn_clear_search = ctk.CTkButton(
            search_wrap,
            text="✕",
            width=32,
            height=32,
            font=T.FONT_SMALL,
            fg_color=T.BG_HOVER,
            hover_color=T.BORDER,
            command=self._clear_search,
        )
        self.btn_clear_search.grid(row=0, column=1, padx=(6, 0))

        filters = ctk.CTkFrame(toolbar, fg_color="transparent")
        filters.grid(row=1, column=0, columnspan=2, sticky="ew")
        filters.grid_columnconfigure(0, weight=1)

        self.category_box = ctk.CTkComboBox(
            filters,
            values=["Все категории"],
            width=180,
            height=40,
            font=T.FONT_SMALL,
            fg_color=T.BG_INPUT,
            border_color=T.BORDER,
            command=self._on_filter,
        )
        self.category_box.grid(row=0, column=0, sticky="w", padx=(0, T.PAD_SM))
        self.category_box.set("Все категории")

        freq_frame = ctk.CTkFrame(filters, fg_color="transparent")
        freq_frame.grid(row=0, column=1, sticky="w")

        verified_icon = self._keep_icon(ui_icon("frequent", T.ICON_SM))
        if verified_icon:
            ctk.CTkLabel(freq_frame, text="", image=verified_icon).pack(
                side="left", padx=(0, 4)
            )

        self.frequent_only = ctk.CTkCheckBox(
            freq_frame,
            text="Частые",
            font=T.FONT_SMALL,
            text_color=T.TEXT_SECONDARY,
            command=self._on_filter,
        )
        self.frequent_only.pack(side="left")

        self.btn_reset_filters = ctk.CTkButton(
            freq_frame,
            text="Снять фильтр",
            width=120,
            height=30,
            font=T.FONT_TINY,
            fg_color=T.BG_HOVER,
            hover_color=T.BORDER,
            command=self._reset_filters,
        )
        self.btn_reset_filters.pack(side="left", padx=(8, 0))

        # Ряд чипов активных фильтров (снимаются по отдельности)
        self._chips_container = ctk.CTkFrame(toolbar, fg_color="transparent")
        self._chips_container.grid(row=2, column=0, columnspan=2, sticky="ew")
        self._chips_container.grid_remove()  # скрыт, пока нет активных фильтров
        self._update_filter_chips()

        self._db_list_panel = ctk.CTkFrame(
            db,
            fg_color=T.BG_PANEL,
            corner_radius=T.RADIUS,
            border_width=1,
            border_color=T.BORDER,
        )
        self._db_list_panel.grid(
            row=1, column=0, sticky="nsew", padx=(T.PAD, T.PAD_SM), pady=(0, T.PAD)
        )
        self._db_list_panel.grid_rowconfigure(0, weight=1)
        self._db_list_panel.grid_columnconfigure(0, weight=1)

        self.scroll_list = ctk.CTkScrollableFrame(self._db_list_panel, fg_color="transparent")
        self.scroll_list.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        self._db_detail_panel = ctk.CTkFrame(
            db,
            fg_color=T.BG_PANEL,
            corner_radius=T.RADIUS,
            border_width=1,
            border_color=T.BORDER,
        )
        self._db_detail_panel.grid(
            row=1, column=1, sticky="nsew", padx=(T.PAD_SM, T.PAD), pady=(0, T.PAD)
        )
        self._db_detail_panel.grid_rowconfigure(2, weight=1)
        self._db_detail_panel.grid_columnconfigure(0, weight=1)
        detail_panel = self._db_detail_panel

        self.detail_title = ctk.CTkLabel(
            detail_panel,
            text="Выберите запись",
            font=("Segoe UI", 17, "bold"),
            text_color=T.TEXT_PRIMARY,
            anchor="w",
            justify="left",
        )
        self.detail_title.grid(row=0, column=0, sticky="ew", padx=T.PAD, pady=(T.PAD, 2))

        self.detail_meta = ctk.CTkLabel(
            detail_panel,
            text="",
            font=T.FONT_TINY,
            text_color=T.TEXT_MUTED,
            anchor="w",
            justify="left",
        )
        self.detail_meta.grid(row=1, column=0, sticky="ew", padx=T.PAD, pady=(0, 4))

        self._adaptive.track(self.detail_title, detail_panel, padding=T.PAD * 2)
        self._adaptive.track(self.detail_meta, detail_panel, padding=T.PAD * 2)
        self._detail_loader = LoadingDots(self.detail_title)

        self.textbox = ctk.CTkTextbox(
            detail_panel,
            font=T.FONT_BODY,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER,
            text_color=T.TEXT_PRIMARY,
            wrap="word",
        )
        self.textbox.grid(row=2, column=0, sticky="nsew", padx=T.PAD, pady=T.PAD_SM)
        self.textbox.configure(state="disabled")

        actions = ctk.CTkFrame(detail_panel, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=T.PAD, pady=(0, T.PAD))

        copy_icon = self._keep_icon(ui_icon("copy", T.ICON_MD))
        ctk.CTkButton(
            actions,
            text="Копировать",
            image=copy_icon,
            compound="left",
            width=140,
            height=36,
            font=T.FONT_SMALL,
            fg_color=T.BG_HOVER,
            hover_color=T.BORDER,
            command=self.copy_law_text,
        ).pack(side="left")

        star_icon = self._keep_icon(ui_icon("frequent", T.ICON_MD))
        ctk.CTkButton(
            actions,
            text="В избранное",
            image=star_icon,
            compound="left",
            width=150,
            height=36,
            font=T.FONT_SMALL,
            fg_color=T.BG_HOVER,
            hover_color=T.BORDER,
            command=self._add_current_to_favorites,
        ).pack(side="left", padx=(8, 0))

        ai_icon = self._keep_icon(ui_icon("ai", T.ICON_MD))
        self.btn_ai = ctk.CTkButton(
            actions,
            text="Отыграть ИИ",
            image=ai_icon,
            compound="left",
            width=150,
            height=36,
            font=T.FONT_SMALL,
            command=self.trigger_ai_action,
        )
        self.btn_ai.pack(side="right")

        self.status_bar = ctk.CTkLabel(
            db, text="Ctrl+F — поиск  ·  ↑↓ — навигация  ·  Esc — сброс  ·  фильтры — чипами ✕",
            font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w",
        )
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=T.PAD, pady=(0, 8))

    def _update_header_faction_icon(self):
        icon = faction_icon(self.current_faction["id"], T.ICON_LG)
        if icon:
            self._keep_icon(icon)
            self.header_faction_icon.configure(image=icon)
        else:
            self.header_faction_icon.configure(image=None)
        self.faction_title.configure(text=self.current_faction["name"])

    def _update_compact_faction_icon(self):
        icon = faction_icon(self.current_faction["id"], T.ICON_MD)
        if icon:
            self._keep_icon(icon)
            self.compact_faction_icon.configure(image=icon)
        else:
            self.compact_faction_icon.configure(image=None)

    def _bind_resize(self):
        def on_root_configure(event):
            if event.widget is self.root:
                self._adaptive.schedule()

        self.root.bind("<Configure>", on_root_configure, add="+")

    def _schedule_update_checks(self):
        cfg = app_config.get("updates", {}) or {}
        if not cfg.get("auto_check", True):
            return
        hours = max(1, int(cfg.get("check_interval_hours", 24)))
        interval_ms = hours * 3600 * 1000
        self.root.after(interval_ms, self._periodic_update_check)

    def _periodic_update_check(self):
        self._run_update_check(force=False)
        self._schedule_update_checks()

    def _run_update_check(self, force: bool = False):
        def worker():
            from core.updates import check_for_updates, get_update_status_text

            info = check_for_updates(force=force)

            def on_ui():
                if info and info.available:
                    self._show_update_notification(info)
                elif force:
                    msg = get_update_status_text(info)
                    self.page_settings.set_update_status(msg, ok=not (info and info.available))
                    show_toast(self.root, msg, accent=self.accent)
                elif info:
                    self.page_settings.set_update_status(get_update_status_text(info))

            self.root.after(0, on_ui)

        threading.Thread(target=worker, daemon=True).start()

    def _show_update_notification(self, info):
        self._pending_update = info
        self.update_badge.configure(text="● Обновление")
        self.update_badge.pack(side="left", padx=(8, 0))
        self.page_settings.set_update_status(
            f"Доступно обновление {info.latest} (у вас {info.current})", ok=False,
        )
        show_toast(self.root, f"Доступна версия {info.latest}", accent=T.WARNING)
        if self._badge_pulse:
            self._badge_pulse.start()

        cfg = app_config.get("updates", {}) or {}
        if cfg.get("auto_download", True) and info.download_url:
            self._auto_download_update(info)
        else:
            show_update_dialog(self.root, info, on_dismiss=self._clear_update_badge, accent=self.accent)

    def _auto_download_update(self, info):
        def worker():
            from core.update_installer import UpdateInstallError, cached_update_path, download_update

            existing = cached_update_path(info)
            if existing:
                self.root.after(0, lambda: self._open_update_dialog(info, existing))
                return
            try:
                path = download_update(info)
                self.root.after(0, lambda: self._open_update_dialog(info, path))
            except UpdateInstallError:
                self.root.after(0, lambda: show_update_dialog(
                    self.root, info, on_dismiss=self._clear_update_badge, accent=self.accent,
                ))

        threading.Thread(target=worker, daemon=True).start()

    def _open_update_dialog(self, info, package_path):
        show_toast(self.root, "Обновление загружено — установите одним кликом", accent=T.SUCCESS)
        show_update_dialog(
            self.root, info, package_path=package_path,
            on_dismiss=self._clear_update_badge, accent=self.accent,
        )

    def _clear_update_badge(self):
        self._pending_update = None
        if self._badge_pulse:
            self._badge_pulse.stop()
        self.update_badge.pack_forget()

    def _bind_keyboard_shortcuts(self):
        def focus_search(e):
            if self.current_page == "database":
                self.search_entry.focus_set()
            elif self.current_page == "measures":
                self.page_measures.search.focus_set()

        self.root.bind("<Control-f>", focus_search)
        self.root.bind("<Escape>", lambda e: self._clear_search())
        self.root.bind("<Up>", lambda e: self._navigate_list(-1))
        self.root.bind("<Down>", lambda e: self._navigate_list(1))

    def _navigate_list(self, delta: int):
        if self.current_page == "measures":
            self.page_measures.navigate_list(delta)
            return
        if self.current_page != "database" or not self.filtered_items:
            return
        self._list_index = max(0, min(len(self.filtered_items) - 1, self._list_index + delta))
        item = self.filtered_items[self._list_index]
        self._show_item(item, self._item_key(item))

    def toggle_hidden(self):
        """Полное скрытие окна (не compact)."""
        if self.is_hidden:
            self.root.deiconify()
            self._set_topmost(True)
            self.is_hidden = False
            show_toast(self.root, "HelpeRP снова на экране", accent=self.accent)
        else:
            self.root.withdraw()
            self.is_hidden = True

    def _open_settings(self):
        if not self.is_expanded:
            self._set_mode(True)
        self._switch_page("settings")

    def _preview_theme(self):
        vals = self.page_settings.theme_picker.get_values()
        ui = dict(app_config.get("ui", {}) or {})
        ui.update(vals)
        app_config.settings["ui"] = ui
        from gui.theme_engine import load_theme_from_config
        load_theme_from_config()
        self.apply_visual_theme()

    def apply_visual_theme(self):
        from gui.theme_engine import effective_accent

        self.accent, self._accent_hover = effective_accent(self.current_faction["accent"])

        self.root.configure(fg_color=T.BG_ROOT)
        self.compact_frame.configure(fg_color=T.BG_SIDEBAR, border_color=T.BORDER)
        self.expanded_frame.configure(fg_color=T.BG_ROOT)
        self.sidebar.configure(fg_color=T.BG_SIDEBAR)
        self.main.configure(fg_color=T.BG_ROOT)

        self.compact_search.configure(fg_color=T.BG_INPUT, border_color=T.BORDER)
        self.compact_preview.configure(text_color=T.TEXT_MUTED)
        self.compact_stats.configure(text_color=T.TEXT_MUTED)
        self._sidebar_footer.configure(fg_color=T.BG_CARD)
        self.character_box.configure(fg_color=T.BG_INPUT, border_color=T.BORDER)

        self.search_entry.configure(fg_color=T.BG_INPUT, border_color=T.BORDER)
        self.category_box.configure(fg_color=T.BG_INPUT, border_color=T.BORDER)
        self._db_list_panel.configure(fg_color=T.BG_PANEL, border_color=T.BORDER)
        self._db_detail_panel.configure(fg_color=T.BG_PANEL, border_color=T.BORDER)
        self.textbox.configure(fg_color=T.BG_CARD, border_color=T.BORDER, text_color=T.TEXT_PRIMARY)
        self.detail_meta.configure(text_color=T.TEXT_MUTED)
        self.stats_label.configure(text_color=T.TEXT_SECONDARY)
        self.faction_sub.configure(text_color=T.TEXT_MUTED)
        self.faction_title.configure(text_color=T.TEXT_PRIMARY)
        self.status_bar.configure(text_color=T.TEXT_MUTED)

        for name, btn in self.nav_buttons.items():
            selected = name == self.current_page
            btn.configure(
                fg_color=T.BG_SELECTED if selected else T.BG_CARD,
                hover_color=T.BG_HOVER,
                border_color=self.accent if selected else T.BORDER,
            )

        for name, btn in self.faction_buttons.items():
            fac = get_faction(name)
            selected = name == self.current_faction["name"]
            btn.configure(
                fg_color=T.BG_SELECTED if selected else T.BG_CARD,
                hover_color=T.BG_HOVER,
                border_color=fac["accent"] if selected else T.BORDER,
            )

        # Применить тему только к уже созданным страницам
        if self._page_measures is not None:
            self._page_measures.apply_theme(self.accent)
        if self._page_templates is not None:
            self._page_templates.apply_theme(self.accent)
        if self._page_settings is not None:
            self._page_settings.apply_theme(self.accent)
        self._apply_accent()
        self._refresh_list()
        self._refresh_recent_sidebar()

    def _on_settings_saved(self):
        hk = app_config.get("hotkeys", {})
        self.hotkey_label.configure(text=f"{hk.get('toggle_overlay', 'shift+\\\\').upper()} — режим")
        self.hide_hotkey_label.configure(
            text=f"{hk.get('hide_window', 'ctrl+shift+h').upper()} — скрыть окно"
        )
        ui_cfg = app_config.get("ui", {})
        self.list_limit = int(ui_cfg.get("list_limit", 120))
        self.page_measures.set_list_limit(self.list_limit)
        self._refresh_character_box()
        from gui.theme_engine import load_theme_from_config
        load_theme_from_config()
        self.apply_visual_theme()
        from core.ai_client import rp_ai
        rp_ai.update_client()
        from core.discord_presence import refresh_discord_presence
        refresh_discord_presence()

    def _reset_filters(self):
        self.search_entry.delete(0, "end")
        self.category_box.set("Все категории")
        if self.frequent_only.get():
            self.frequent_only.deselect()
        self._active_filters.clear()
        self._update_filter_chips()
        self._on_filter()

    def _clear_search(self):
        self._reset_filters()

    def _update_filter_chips(self):
        """Перерисовать чипы активных фильтров (каждый снимается отдельно)."""
        container = getattr(self, "_chips_container", None)
        if container is None:
            return
        for child in container.winfo_children():
            child.destroy()
        self._chip_buttons.clear()
        if not self._active_filters:
            container.grid_remove()
            return
        for key, label in self._active_filters.items():
            btn = ctk.CTkButton(
                container,
                text=f"{label}  ✕",
                height=26,
                font=T.FONT_TINY,
                fg_color=T.BG_CARD,
                hover_color=T.BORDER,
                text_color=self.accent,
                corner_radius=13,
                command=lambda k=key: self._remove_filter_chip(k),
            )
            btn.pack(side="left", padx=(0, 6), pady=(4, 0))
            self._chip_buttons[key] = btn
        container.grid()

    def _remove_filter_chip(self, key: str):
        """Снять один конкретный фильтр (чип) и перефильтровать."""
        if key == "query":
            self.search_entry.delete(0, "end")
        elif key == "category":
            self.category_box.set("Все категории")
        elif key == "frequent":
            self.frequent_only.deselect()
        self._active_filters.pop(key, None)
        self._on_filter()

    def _set_mode(self, expanded: bool):
        if expanded == self.is_expanded:
            return

        if animations_enabled():
            target = T.EXPANDED_SIZE if expanded else T.COMPACT_SIZE

            def mid():
                if expanded:
                    self.compact_frame.pack_forget()
                    self.expanded_frame.pack(fill="both", expand=True)
                    q = self.compact_search.get().strip()
                    if q:
                        self.search_entry.delete(0, "end")
                        self.search_entry.insert(0, q)
                        self._on_filter()
                else:
                    self.saved_geometry = self.root.geometry()
                    q = self.search_entry.get().strip()
                    self.compact_search.delete(0, "end")
                    if q:
                        self.compact_search.insert(0, q)
                    self.expanded_frame.pack_forget()
                    self.compact_frame.pack(fill="x", padx=8, pady=8)

            def done():
                self.is_expanded = expanded
                if expanded:
                    if self.saved_geometry:
                        self.root.geometry(self.saved_geometry)
                    else:
                        self._center_geometry(*T.EXPANDED_SIZE)
                    self.root.minsize(960, 600)
                else:
                    self.root.minsize(T.COMPACT_SIZE[0], T.COMPACT_SIZE[1])
                    self._update_compact_bar()
                if animations_enabled():
                    Animator.flash_bar(self.accent_bar, self.root, self.accent)

            Animator.animate_geometry(self.root, target[0], target[1], on_mid=mid, on_done=done)
            return

        self._apply_mode(expanded)

    def _apply_mode(self, expanded: bool):
        if expanded:
            self.compact_frame.pack_forget()
            self.expanded_frame.pack(fill="both", expand=True)
            q = self.compact_search.get().strip()
            if q:
                self.search_entry.delete(0, "end")
                self.search_entry.insert(0, q)
                self._on_filter()
            if self.saved_geometry:
                self.root.geometry(self.saved_geometry)
            else:
                self._center_geometry(*T.EXPANDED_SIZE)
            self.root.minsize(960, 600)
        else:
            self.saved_geometry = self.root.geometry()
            q = self.search_entry.get().strip()
            self.compact_search.delete(0, "end")
            if q:
                self.compact_search.insert(0, q)
            self.expanded_frame.pack_forget()
            self.compact_frame.pack(fill="x", padx=8, pady=8)
            self._center_geometry(*T.COMPACT_SIZE)
            self.root.minsize(T.COMPACT_SIZE[0], T.COMPACT_SIZE[1])
            self._update_compact_bar()

        self.is_expanded = expanded

    def _update_compact_bar(self):
        total = len(self.all_items)
        self.compact_stats.configure(text=f"{total} зап.")
        self._update_compact_faction_icon()
        if self.current_item:
            t = self.current_item.get("title", "")
            self.compact_preview.configure(text=t[:55] + ("…" if len(t) > 55 else ""))
        elif self.filtered_items:
            self.compact_preview.configure(
                text=(
                    f"Найдено: {len(self.filtered_items)} · "
                    f"{self.filtered_items[0].get('title', '')[:30]}…"
                )
            )
        else:
            self.compact_preview.configure(
                text=self.current_faction.get("subtitle", "")
            )

    def _on_compact_search(self, event=None):
        q = self.compact_search.get().strip()
        if not q:
            self.filtered_items = list(self.all_items)
        else:
            self.filtered_items = filter_and_rank(self.all_items, q)
        self._list_index = 0
        if self.filtered_items:
            self.current_item = self.filtered_items[0]
        self._update_compact_bar()

    def _apply_accent(self):
        from gui.theme_engine import effective_accent

        self.accent, hover = effective_accent(self.current_faction["accent"])
        self._accent_hover = hover
        self.accent_bar.configure(fg_color=self.accent)
        self.compact_accent.configure(fg_color=self.accent)
        self.frequent_only.configure(fg_color=self.accent, hover_color=hover)
        self.btn_ai.configure(fg_color=self.accent, hover_color=hover)
        self.btn_expand.configure(fg_color=self.accent, hover_color=hover)
        self.detail_title.configure(text_color=self.accent)
        # Только для уже созданных страниц
        if self._page_measures is not None:
            self._page_measures.set_accent(self.accent)
        if self._page_templates is not None:
            self._page_templates.set_accent(self.accent)
        if self._page_settings is not None:
            self._page_settings.set_accent(self.accent)
        for name, btn in self.nav_buttons.items():
            if name == self.current_page:
                btn.configure(border_color=self.accent)

    def _select_faction(self, faction):
        if self.current_page != "database":
            self._switch_page("database")

        app_config.set("current_faction", faction["name"])
        self.current_faction = faction
        self.search_entry.delete(0, "end")
        self.compact_search.delete(0, "end")
        self.category_box.set("Все категории")
        self.frequent_only.deselect()

        for name, btn in self.faction_buttons.items():
            fac = get_faction(name)
            selected = name == faction["name"]
            btn.configure(
                fg_color=T.BG_SELECTED if selected else T.BG_CARD,
                border_width=2 if selected else 0,
                border_color=fac["accent"] if selected else T.BORDER,
            )

        # Загрузить данные новой фракции асинхронно
        self._load_faction_data_async(faction["name"])
        self._apply_accent()
        self._update_header_faction_icon()
        if animations_enabled():
            Animator.flash_bar(self.accent_bar, self.root, self.accent)
        self.faction_sub.configure(text=faction.get("subtitle", ""))
        self._clear_detail()
        self._update_compact_bar()

    def _load_faction_data_async(self, faction_name):
        """Загрузить данные фракции в фоне."""
        def worker():
            try:
                items, faction = load_faction_items(faction_name)
                self.root.after(0, lambda: self._on_data_loaded(items, faction))
            except Exception as e:
                print(f"[Data] Ошибка загрузки фракции {faction_name}: {e}")
                self.root.after(0, lambda: self._on_data_loaded([], get_faction(faction_name)))

        threading.Thread(target=worker, daemon=True, name=f"faction-loader-{faction_name}").start()

    def _update_categories(self):
        cats = sorted({i.get("category") for i in self.all_items if i.get("category")})
        self.category_box.configure(values=["Все категории"] + cats)
        self.category_box.set("Все категории")

    def _item_search_blob(self, item):
        return item_blob(item)

    def _stats_text(self):
        total = len(self.all_items)
        freq = sum(1 for x in self.all_items if x.get("is_frequent"))
        shown = len(self.filtered_items)
        label = self.current_faction.get("entry_label", "записей")
        if shown != total:
            return f"{shown} / {total} {label}  ·  {freq} частых"
        return f"{total} {label}  ·  {freq} частых"

    def _item_key(self, item):
        return item.get("id") or item.get("article") or item.get("title")

    def _push_recent(self, item):
        key = self._item_key(item)
        title = item.get("title", "")
        recent = [r for r in app_config.get("recent", []) if r.get("key") != key]
        recent.insert(0, {"key": key, "title": title, "faction": self.current_faction["name"]})
        app_config.set("recent", recent[:12])
        self._refresh_recent_sidebar()

    def _add_current_to_favorites(self):
        if not self.current_item:
            return
        item = self.current_item
        key = self._item_key(item)
        title = item.get("title", "—")
        config = app_config.get("favorites", {}) or {}
        favorites = config.get("items", []) if isinstance(config.get("items", []), list) else []
        favorites = [x for x in favorites if isinstance(x, dict) and x.get("key") != key]
        favorites.insert(0, {
            "key": key,
            "title": title,
            "faction": self.current_faction.get("name", "Все базы"),
            "category": item.get("category", ""),
        })
        max_items = max(1, int(config.get("max_items", 8) or 8))
        app_config.set("favorites", {
            "items": favorites[:max_items],
            "hotkey": config.get("hotkey") or "ctrl+alt+f",
            "mode": config.get("mode") or "compact",
            "max_items": max_items,
        })
        show_toast(self.root, "Добавлено в избранное", accent=self.accent)

    def _favorites_for_overlay(self):
        cfg = app_config.get("favorites", {}) or {}
        items = cfg.get("items", []) if isinstance(cfg.get("items", []), list) else []
        return [x for x in items if isinstance(x, dict)]

    def toggle_favorites_overlay(self):
        if self.favorites_overlay is None or not self.favorites_overlay.winfo_exists():
            self.favorites_overlay = ctk.CTkToplevel(self.root)
            self.favorites_overlay.withdraw()
            self.favorites_overlay.attributes("-topmost", False)
            self.favorites_overlay.overrideredirect(True)
            self.favorites_overlay.configure(fg_color=T.BG_PANEL)
            self.favorites_overlay.grid_columnconfigure(0, weight=1)
            self.favorites_overlay.grid_rowconfigure(0, weight=1)

            self._favorites_overlay_frame = ctk.CTkScrollableFrame(
                self.favorites_overlay, fg_color=T.BG_PANEL, corner_radius=T.RADIUS,
            )
            self._favorites_overlay_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
            self._favorites_overlay_frame.grid_columnconfigure(0, weight=1)
        self._refresh_favorites_overlay()
        if self.favorites_overlay.winfo_ismapped():
            self.favorites_overlay.withdraw()
        else:
            self.favorites_overlay.deiconify()
            self.favorites_overlay.focus_set()
            self.favorites_overlay.geometry(self._favorites_overlay_geometry())

    def _favorites_overlay_geometry(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = min(420, sw - 60)
        h = min(330, sh - 120)
        x = max(20, sw - w - 30)
        y = max(20, 40)
        return f"{w}x{h}+{x}+{y}"

    def _refresh_favorites_overlay(self):
        frame = getattr(self, "_favorites_overlay_frame", None)
        if frame is None:
            return
        for child in frame.winfo_children():
            child.destroy()

        items = self._favorites_for_overlay()
        if not items:
            ctk.CTkLabel(
                frame, text="Избранное пусто\n\nДобавьте статьи в списке кнопкой 'В избранное'",
                font=T.FONT_SMALL, text_color=T.TEXT_MUTED, justify="left", anchor="w",
            ).pack(anchor="w", padx=12, pady=14)
            return

        mode = (app_config.get("favorites", {}) or {}).get("mode", "compact")
        title = "Избранные статьи" if mode != "faction" else "Статьи подразделения"
        ctk.CTkLabel(frame, text=title.upper(), font=T.FONT_TINY, text_color=self.accent, anchor="w").pack(anchor="w", padx=12, pady=(12, 8))
        for item in items:
            text = item.get("title", "—")
            ctk.CTkButton(
                frame,
                text=text,
                anchor="w",
                height=34,
                font=T.FONT_SMALL,
                fg_color=T.BG_CARD,
                hover_color=T.BG_HOVER,
                text_color=T.TEXT_PRIMARY,
                corner_radius=T.RADIUS_SM,
                command=lambda i=item: self._open_favorite_from_overlay(i),
            ).pack(fill="x", padx=12, pady=2)

    def _open_favorite_from_overlay(self, item):
        key = item.get("key")
        if not key:
            return
        target_faction = get_faction(item.get("faction") or self.current_faction["name"])
        self._select_faction(target_faction)
        for entry in self.all_items:
            if self._item_key(entry) == key:
                self._show_item(entry, key)
                return

    def _on_search_typed(self, event=None):
        """Debounce: пересчёт поиска только после паузы в наборе."""
        if self._filter_after:
            self.root.after_cancel(self._filter_after)
        self._filter_after = self.root.after(150, self._on_filter)

    def _apply_filter_now(self):
        """Синхронная фильтрация (для кнопок/чипов, без debounce)."""
        self._on_filter()

    def _on_filter(self, event=None):
        if self._filter_after:
            self.root.after_cancel(self._filter_after)
            self._filter_after = None
        query = self.search_entry.get().strip()
        cat = self.category_box.get()
        pool = self.all_items
        self.list_show_all = False

        # Запомнить активные фильтры для чипов
        active = {}
        if query:
            active["query"] = query
        if cat and cat != "Все категории":
            active["category"] = cat
        if self.frequent_only.get():
            active["frequent"] = "Частые"
        self._active_filters = active
        self._update_filter_chips()

        if self.frequent_only.get():
            pool = [x for x in pool if x.get("is_frequent")]
        if cat and cat != "Все категории":
            pool = [x for x in pool if x.get("category") == cat]
        if query:
            pool = filter_and_rank(pool, query)

        self.filtered_items = pool
        self._list_index = 0
        self._refresh_list()
        self.stats_label.configure(text=self._stats_text())
        self._update_compact_bar()

        if query and len(pool) == 0 and len(query) > 3:
            if app_config.get("search", {}).get("online_fallback", True):
                self._online_search(query)

    def _refresh_list(self):
        for w in self.scroll_list.winfo_children():
            w.destroy()
        self.list_buttons.clear()

        if not self.filtered_items:
            empty = ctk.CTkFrame(self.scroll_list, fg_color="transparent")
            empty.pack(fill="x", pady=40)

            warn_icon = ui_icon("warning", T.ICON_LG)
            if warn_icon:
                self._keep_icon(warn_icon)
                ctk.CTkLabel(empty, text="", image=warn_icon).pack(pady=(0, 8))

            ctk.CTkLabel(
                empty,
                text="Ничего не найдено",
                font=T.FONT_BODY,
                text_color=T.TEXT_MUTED,
            ).pack()
            ctk.CTkLabel(
                empty,
                text="Измените фильтры или попробуйте другой запрос",
                font=T.FONT_TINY,
                text_color=T.TEXT_MUTED,
            ).pack(pady=(4, 0))
            if self._active_filters:
                ctk.CTkButton(
                    empty,
                    text="Сбросить фильтры",
                    width=140,
                    height=30,
                    font=T.FONT_TINY,
                    fg_color=T.BG_HOVER,
                    hover_color=T.BORDER,
                    command=self._reset_filters,
                ).pack(pady=(12, 0))
            return

        verified = ui_icon("frequent", T.ICON_SM)
        if verified:
            self._keep_icon(verified)

        display = self.filtered_items
        if not self.list_show_all and len(display) > self.list_limit:
            display = display[: self.list_limit]

        for idx, item in enumerate(display):
            key = self._item_key(item)
            title = item.get("title", "—")
            short = title if len(title) <= 48 else title[:45] + "…"
            cat = item.get("category", "")
            sub = f"\n{cat}" if cat and cat != "Словарь терминов" else ""
            is_freq = item.get("is_frequent")
            btn_image = verified if is_freq else None

            btn = ctk.CTkButton(
                self.scroll_list,
                text=f"{short}{sub}",
                image=btn_image,
                compound="left" if btn_image else "center",
                anchor="w",
                height=44 if sub else 38,
                font=T.FONT_SMALL,
                fg_color=T.BG_CARD,
                hover_color=T.BG_HOVER,
                text_color=T.TEXT_PRIMARY,
                corner_radius=T.RADIUS_SM,
                command=lambda i=item, k=key: self._show_item(i, k),
            )
            btn.pack(fill="x", pady=2)
            self.list_buttons[key] = btn

        if not self.list_show_all and len(self.filtered_items) > self.list_limit:
            rest = len(self.filtered_items) - self.list_limit
            ctk.CTkButton(
                self.scroll_list,
                text=f"Показать ещё {rest}…",
                height=36,
                font=T.FONT_TINY,
                fg_color=T.BG_HOVER,
                hover_color=T.BORDER,
                command=self._show_all_list,
            ).pack(fill="x", pady=6)

        if self.filtered_items:
            idx = min(self._list_index, len(self.filtered_items) - 1)
            item = self.filtered_items[idx]
            self._show_item(item, self._item_key(item))

        Animator.stagger_buttons(self.root, list(self.list_buttons.values()))

    def _show_all_list(self):
        self.list_show_all = True
        self._refresh_list()

    def _highlight_selection(self, key):
        for k, btn in self.list_buttons.items():
            if k == key:
                Animator.highlight_button(btn, self.root, self.accent)
            else:
                btn.configure(fg_color=T.BG_CARD, border_width=0)

    def _build_detail_body(self, item):
        lines = []
        body = item.get("description") or item.get("protocol") or item.get("text", "")
        if body:
            lines.append(body)
        if item.get("punishment"):
            lines.append(f"\n\n▸ Наказание / меры\n{item['punishment']}")
        if item.get("chapter"):
            lines.append(f"\n\n▸ {item['chapter']}")
        if item.get("source_faction"):
            lines.append(f"\n\n▸ Фракция: {item['source_faction']}")
        if item.get("usable_by"):
            lines.append(f"\n\n▸ Применяют: {', '.join(item['usable_by'])}")
        if item.get("keywords"):
            lines.append(
                f"\n\n▸ Ключевые слова: {', '.join(item['keywords'][:14])}"
            )
        return "".join(lines)

    def _show_item(self, item, key):
        self.current_item = item
        self.selected_list_key = key
        self._list_index = self.filtered_items.index(item) if item in self.filtered_items else 0
        self._push_recent(item)
        self._highlight_selection(key)

        self.detail_title.configure(text=item.get("title", "—"))
        meta = []
        if item.get("category"):
            meta.append(item["category"])
        if item.get("article"):
            meta.append(f"№{item['article']}")
        if item.get("source_faction"):
            meta.append(item["source_faction"])
        if item.get("is_frequent"):
            meta.append("Частая")
        self.detail_meta.configure(text="  ·  ".join(meta))
        self._adaptive.schedule()

        self.textbox.configure(state="normal")
        self.textbox.delete("0.0", "end")
        self.textbox.insert("0.0", self._build_detail_body(item))
        self.textbox.configure(state="disabled")
        self._update_compact_bar()

        if animations_enabled():
            Animator.color_pulse(
                self.textbox, self.root, T.BORDER, self.accent, duration=220, cycles=1,
            )

    def _clear_detail(self):
        self.current_item = None
        self.selected_list_key = None
        self.detail_title.configure(text="Выберите запись")
        self.detail_meta.configure(text="")
        self.textbox.configure(state="normal")
        self.textbox.delete("0.0", "end")
        self.textbox.configure(state="disabled")

    def _online_search(self, query):
        if self._detail_loader:
            self._detail_loader.start("Поиск в интернете")
        else:
            self.detail_title.configure(text="Поиск в интернете…")
        self.detail_meta.configure(text="Wikipedia · DuckDuckGo")

        def worker():
            try:
                from core.online_search import search_law_online

                txt = search_law_online(query, self.current_faction["name"])

                def finish():
                    if self._detail_loader:
                        self._detail_loader.stop()
                    if txt:
                        self._show_online(query, txt)
                    else:
                        self.detail_title.configure(text="Не найдено")
                        self.detail_meta.configure(text="")

                self.root.after(0, finish)
            except Exception as e:
                print(f"Ошибка поиска: {e}")
                if self._detail_loader:
                    self.root.after(0, lambda: self._detail_loader.stop("Ошибка поиска"))

        threading.Thread(target=worker, daemon=True).start()

    def _show_online(self, query, text):
        self.current_item = {"title": query, "description": text}
        self.detail_title.configure(text=f"Из сети: {query}")
        self.detail_meta.configure(text="Онлайн-поиск")
        self.textbox.configure(state="normal")
        self.textbox.delete("0.0", "end")
        self.textbox.insert("0.0", text)
        self.textbox.configure(state="disabled")
        self._update_compact_bar()

    def copy_law_text(self):
        text = self.textbox.get("0.0", "end").strip()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        show_toast(self.root, "Скопировано в буфер обмена", accent=self.accent)

    def trigger_ai_action(self):
        text = self.textbox.get("0.0", "end").strip()
        if not text:
            return
        if not effective_api_key(
            app_config.get("api_key", ""),
            app_config.get("base_url", ""),
            app_config.get("ai_provider", ""),
        ):
            show_toast(self.root, "Настройте API в разделе Настройки → ИИ", accent=T.ERROR)
            self._switch_page("settings")
            return

        if self._detail_loader:
            self._detail_loader.start("ИИ формирует отыгровку")
        else:
            self.detail_title.configure(text="ИИ формирует отыгровку…")
        from core.characters import get_active_character_dict
        char = get_active_character_dict()

        def worker():
            try:
                from core.ai_client import AIClientError, rp_ai

                prompt = (
                    f"Фракция: {self.current_faction['name']}\n"
                    f"Персонаж: {char.get('name', '')}, "
                    f"{char.get('rank', '')}, {char.get('badge', '')}\n"
                    f"Характер: {char.get('personality', '')}\n"
                    f"Сделай отыгровку по тексту:\n{text}"
                )
                lines = rp_ai.generate_rp_commands(prompt)
                title = self.current_item.get("title", "Готово") if self.current_item else "Готово"

                def on_ui():
                    if self._detail_loader:
                        self._detail_loader.stop(title)
                    else:
                        self.detail_title.configure(text=title)
                    if app_config.get("ui", {}).get("auto_send_ai"):
                        from core.hotkeys import send_rp_sequence
                        send_rp_sequence(lines)
                        show_toast(self.root, "Отыгровка отправлена в чат", accent=self.accent)
                    else:
                        AIPreviewDialog(self.root, lines, on_send=lambda ls: self._send_ai_lines(ls))

                self.root.after(0, on_ui)
            except Exception as e:
                msg = str(e)[:120]

                def on_err():
                    if self._detail_loader:
                        self._detail_loader.stop("Ошибка ИИ")
                    else:
                        self.detail_title.configure(text="Ошибка ИИ")
                    show_toast(self.root, msg, accent=T.ERROR)

                self.root.after(0, on_err)

        threading.Thread(target=worker, daemon=True).start()

    def _send_ai_lines(self, lines):
        from core.hotkeys import send_rp_sequence
        send_rp_sequence(lines)
        show_toast(self.root, "Отыгровка отправлена в чат", accent=self.accent)

    def toggle_visibility(self):
        """Shift+\\ — компактный ↔ развёрнутый режим."""
        if self.is_hidden:
            self.toggle_hidden()
        self._set_mode(not self.is_expanded)

    def start(self):
        self.root.mainloop()

    # Properties для ленивого доступа к страницам
    @property
    def page_measures(self):
        if self._page_measures is None:
            self._page_measures = MeasuresPanel(self.pages, accent=self.accent, adaptive=self._adaptive)
            self._page_measures.grid(row=0, column=0, sticky="nsew")
            self._page_measures.grid_remove()
        return self._page_measures

    @property
    def page_templates(self):
        if self._page_templates is None:
            self._page_templates = TemplatesPanel(self.pages, accent=self.accent)
            self._page_templates.grid(row=0, column=0, sticky="nsew")
            self._page_templates.grid_remove()
        return self._page_templates

    @property
    def page_settings(self):
        if self._page_settings is None:
            self._page_settings = SettingsPanel(
                self.pages,
                on_saved=self._on_settings_saved,
                on_check_updates=self._run_update_check,
                on_theme_preview=self._preview_theme,
                accent=self.accent,
            )
            self._page_settings.grid(row=0, column=0, sticky="nsew")
            self._page_settings.grid_remove()
        return self._page_settings
