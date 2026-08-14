"""Встроенная панель настроек."""

import threading

import customtkinter as ctk

from core.config import app_config, is_placeholder_api_key
from core.characters import (
    delete_character,
    get_active_character,
    list_characters,
    save_character,
    set_active_character,
)
from core.licensing import (
    activate_license,
    get_machine_code_display,
    is_licensed,
    license_status_text,
    license_key_error_hint,
    validate_license_key,
)
from core.version import (
    COPYRIGHT, DOCS_URL, EULA_VERSION, PRODUCT_EDITION, PRODUCT_NAME,
    PURCHASE_URL, SUPPORT_EMAIL, UPDATE_MANIFEST_URL, VERSION, WEBSITE,
)
from gui import theme as T
from gui.docs_dialog import show_docs
from gui.eula_dialog import show_eula
from gui.ai_provider_picker import AIProviderPicker
from gui.theme_picker import ThemePicker
from gui.toast import show_toast


class SettingsPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_saved=None,
        on_check_updates=None,
        on_theme_preview=None,
        accent: str = T.DEFAULT_ACCENT,
        **kwargs,
    ):
        super().__init__(master, fg_color=T.BG_ROOT, **kwargs)
        self.on_saved = on_saved
        self.on_check_updates = on_check_updates
        self.on_theme_preview = on_theme_preview
        self.accent = accent
        self._sections: list = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_form()
        self._build_actions()

    def set_accent(self, color: str):
        self.accent = color
        self.save_btn.configure(fg_color=color, hover_color=T.DEFAULT_ACCENT_HOVER)
        for cb in self._accent_checkboxes():
            cb.configure(fg_color=color, hover_color=T.DEFAULT_ACCENT_HOVER)
        if hasattr(self, "theme_picker"):
            self.theme_picker.set_accent(color)

    def _accent_checkboxes(self):
        for name in (
            "auto_ai", "ui_animations", "wikipedia_search",
            "online_fallback", "rag_search", "auto_update", "auto_download",
        ):
            cb = getattr(self, name, None)
            if isinstance(cb, ctk.CTkCheckBox):
                yield cb

    def apply_theme(self, accent: str | None = None):
        if accent:
            self.accent = accent
        self.configure(fg_color=T.BG_ROOT)
        for sec in self._sections:
            sec.configure(fg_color=T.BG_PANEL, border_color=T.BORDER)
        if hasattr(self, "_actions_bar"):
            self._actions_bar.configure(fg_color=T.BG_PANEL, border_color=T.BORDER)
        if hasattr(self, "_scroll"):
            self._scroll.configure(scrollbar_button_color=T.BG_HOVER)
        self.save_btn.configure(fg_color=self.accent, hover_color=T.DEFAULT_ACCENT_HOVER)
        for cb in self._accent_checkboxes():
            cb.configure(fg_color=self.accent, hover_color=T.DEFAULT_ACCENT_HOVER)
        if hasattr(self, "theme_picker"):
            self.theme_picker.set_accent(self.accent)
            self.theme_picker._update_swatches()
        if hasattr(self, "ai_picker"):
            self.ai_picker.apply_theme()

    def _section(self, parent, title: str, hint: str = ""):
        wrap = ctk.CTkFrame(parent, fg_color=T.BG_PANEL, corner_radius=T.RADIUS, border_width=1, border_color=T.BORDER)
        wrap.pack(fill="x", pady=(0, T.PAD_SM))
        self._sections.append(wrap)
        inner = ctk.CTkFrame(wrap, fg_color="transparent")
        inner.pack(fill="x", padx=T.PAD, pady=T.PAD_SM)
        ctk.CTkLabel(inner, text=title.upper(), font=T.FONT_TINY, text_color=self.accent, anchor="w").pack(anchor="w")
        if hint:
            ctk.CTkLabel(inner, text=hint, font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w", pady=(2, 8))
        return inner

    def _field(self, parent, label, attr, value="", show=None, placeholder=""):
        ctk.CTkLabel(parent, text=label, font=T.FONT_TINY, text_color=T.TEXT_SECONDARY, anchor="w").pack(
            fill="x", pady=(T.PAD_SM, 2)
        )
        entry = ctk.CTkEntry(
            parent, height=36, font=T.FONT_SMALL, fg_color=T.BG_INPUT, border_color=T.BORDER,
            show=show, placeholder_text=placeholder,
        )
        entry.pack(fill="x", pady=(0, 2))
        if value:
            entry.insert(0, str(value))
        setattr(self, f"_{attr}", entry)

    def _build_form(self):
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=T.BG_HOVER)
        self._scroll.grid(row=0, column=0, sticky="nsew", padx=T.PAD, pady=(0, T.PAD_SM))
        scroll = self._scroll

        ai = self._section(
            scroll, "Искусственный интеллект",
            "Локально (Ollama, LM Studio…) или облако (DeepSeek, OpenRouter…). Данные локально не покидают ПК.",
        )
        self.ai_picker = AIProviderPicker(ai, accent=self.accent, on_test=self._test_api)
        self.ai_picker.pack(fill="x")

        lic = app_config.get("license", {})
        ls = self._section(scroll, "Лицензия", "Коммерческая лицензия · ключ не сохраняется в открытом виде после активации")
        lic_ok = is_licensed(lic)
        self.license_status = ctk.CTkLabel(
            ls, text=license_status_text(lic), font=T.FONT_SMALL,
            text_color=T.SUCCESS if lic_ok else T.TEXT_MUTED, anchor="w",
        )
        self.license_status.pack(anchor="w", pady=(0, 4))

        mc = get_machine_code_display()
        mc_row = ctk.CTkFrame(ls, fg_color="transparent")
        mc_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(mc_row, text=f"ID ПК: {mc}", font=T.FONT_TINY, text_color=T.TEXT_SECONDARY, anchor="w").pack(side="left")
        ctk.CTkButton(
            mc_row, text="Копировать", width=90, height=24, font=T.FONT_TINY,
            fg_color=T.BG_HOVER, command=lambda: self._copy_clip(mc),
        ).pack(side="right")

        self._field(ls, "Новый ключ (если меняете)", "license_key", "", placeholder="HELPE-XXXX-XXXX-XXXXXXXX")
        lic_btns = ctk.CTkFrame(ls, fg_color="transparent")
        lic_btns.pack(fill="x", pady=(4, 0))
        ctk.CTkButton(
            lic_btns, text="EULA", width=80, height=28, font=T.FONT_TINY,
            fg_color=T.BG_HOVER, command=lambda: show_eula(self.winfo_toplevel()),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            lic_btns, text=f"{PURCHASE_URL} · {SUPPORT_EMAIL}",
            font=T.FONT_TINY, text_color=T.TEXT_MUTED,
        ).pack(side="left")

        active = get_active_character()
        self._editing_char_id = active.get("id", "")
        ch = self._section(scroll, "Профили персонажей", "Переключение — в сайдбаре. Для ИИ-отыгровок.")
        prof_row = ctk.CTkFrame(ch, fg_color="transparent")
        prof_row.pack(fill="x", pady=(0, 4))
        labels = [c.get("label", c.get("name", "Персонаж")) for c in list_characters()] or ["Основной"]
        self._char_profile_box = ctk.CTkComboBox(
            prof_row, values=labels, height=34, font=T.FONT_TINY, fg_color=T.BG_INPUT,
            command=self._load_char_profile_fields,
        )
        self._char_profile_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._char_profile_box.set(active.get("label") or labels[0])
        ctk.CTkButton(
            prof_row, text="+", width=36, height=34, font=T.FONT_BODY,
            fg_color=T.BG_HOVER, command=self._new_char_profile,
        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            prof_row, text="−", width=36, height=34, font=T.FONT_BODY,
            fg_color=T.BG_HOVER, command=self._delete_char_profile,
        ).pack(side="left")

        self._field(ch, "Название профиля", "char_label", active.get("label", ""))
        self._field(ch, "Имя", "char_name", active.get("name", ""))
        self._field(ch, "Звание / должность", "char_rank", active.get("rank", ""))
        self._field(ch, "Жетон / №", "char_badge", active.get("badge", ""))
        ctk.CTkLabel(ch, text="Характер и манера речи", font=T.FONT_TINY, text_color=T.TEXT_SECONDARY, anchor="w").pack(
            fill="x", pady=(T.PAD_SM, 2)
        )
        self._char_personality = ctk.CTkTextbox(ch, height=72, font=T.FONT_SMALL, fg_color=T.BG_INPUT, border_color=T.BORDER)
        self._char_personality.pack(fill="x")
        self._char_personality.insert("0.0", active.get("personality", ""))

        game = app_config.get("game", {})
        gm = self._section(scroll, "Игра", "Отправка текста в чат")
        self._field(gm, "Клавиша чата (t, f6…)", "chat_key", game.get("chat_key", "t"))

        hk = app_config.get("hotkeys", {})
        hot = self._section(scroll, "Горячие клавиши")
        self._field(hot, "Компакт ↔ развёрнутый", "hotkey_toggle", hk.get("toggle_overlay", "shift+\\"))
        self._field(hot, "Скрыть / показать окно", "hotkey_hide", hk.get("hide_window", "ctrl+shift+h"))
        self._field(hot, "Показать избранное поверх окна", "favorites_hotkey", hk.get("favorites_overlay", app_config.get("favorites", {}).get("hotkey", "ctrl+alt+f")))

        discord_cfg = app_config.get("discord", {})
        disc = self._section(scroll, "Discord статус", "Показывает активность в Discord с кнопкой-ссылкой")
        self.discord_enabled = ctk.BooleanVar(value=bool(discord_cfg.get("enabled", False)))
        ctk.CTkCheckBox(
            disc, text="Показывать статус в Discord",
            variable=self.discord_enabled, font=T.FONT_SMALL, text_color=T.TEXT_SECONDARY,
            fg_color=self.accent, hover_color=T.DEFAULT_ACCENT_HOVER,
        ).pack(anchor="w", pady=(0, 8))
        self._field(disc, "Client ID Discord", "discord_client_id", str(discord_cfg.get("client_id", "")))
        self._field(disc, "Заголовок активности", "discord_details", str(discord_cfg.get("details", "HelpeRP — база знаний")))
        self._field(disc, "Подзаголовок", "discord_state", str(discord_cfg.get("state", "Режим поиска и подготовки RP")))
        self._field(disc, "Текст кнопки", "discord_button_label", str(discord_cfg.get("button_label", "Открыть HelpeRP")))
        self._field(disc, "Ссылка на кнопку", "discord_button_url", str(discord_cfg.get("button_url", "https://yeolka-lm.github.io/HelpeRP_Client/")))

        ui = app_config.get("ui", {})
        uis = self._section(scroll, "Интерфейс")
        self.theme_picker = ThemePicker(
            uis, accent=self.accent, on_preview=self.on_theme_preview,
        )
        self.theme_picker.pack(fill="x", pady=(0, T.PAD_SM))

        self._field(uis, "Лимит записей в списке (40–500)", "list_limit", str(ui.get("list_limit", 120)))
        self.auto_ai = ctk.BooleanVar(value=ui.get("auto_send_ai", False))
        ctk.CTkCheckBox(
            uis, text="Отправлять ИИ-отыгровку сразу, без предпросмотра",
            variable=self.auto_ai, font=T.FONT_SMALL, text_color=T.TEXT_SECONDARY,
            fg_color=self.accent, hover_color=T.DEFAULT_ACCENT_HOVER,
        ).pack(anchor="w", pady=(T.PAD_SM, 0))
        self.ui_animations = ctk.BooleanVar(value=bool(ui.get("animations", False)))
        ctk.CTkCheckBox(
            uis, text="Плавные анимации интерфейса",
            variable=self.ui_animations, font=T.FONT_SMALL, text_color=T.TEXT_SECONDARY,
            fg_color=self.accent, hover_color=T.DEFAULT_ACCENT_HOVER,
        ).pack(anchor="w", pady=(4, 0))

        sr = app_config.get("search", {})
        search_sec = self._section(scroll, "Поиск", "Wikipedia и онлайн-подсказки")
        self.wikipedia_search = ctk.BooleanVar(value=sr.get("wikipedia", True))
        ctk.CTkCheckBox(
            search_sec, text="Искать в Wikipedia / Викисловаре при онлайн-поиске",
            variable=self.wikipedia_search, font=T.FONT_SMALL, text_color=T.TEXT_SECONDARY,
            fg_color=self.accent, hover_color=T.DEFAULT_ACCENT_HOVER,
        ).pack(anchor="w")
        self.online_fallback = ctk.BooleanVar(value=sr.get("online_fallback", True))
        ctk.CTkCheckBox(
            search_sec, text="Если локально не найдено — искать в интернете",
            variable=self.online_fallback, font=T.FONT_SMALL, text_color=T.TEXT_SECONDARY,
            fg_color=self.accent, hover_color=T.DEFAULT_ACCENT_HOVER,
        ).pack(anchor="w", pady=(4, 0))
        self.rag_search = ctk.BooleanVar(value=sr.get("rag", True))
        ctk.CTkCheckBox(
            search_sec, text="Умный RAG-поиск (BM25) по базе",
            variable=self.rag_search, font=T.FONT_SMALL, text_color=T.TEXT_SECONDARY,
            fg_color=self.accent, hover_color=T.DEFAULT_ACCENT_HOVER,
        ).pack(anchor="w", pady=(4, 0))

        upd = app_config.get("updates", {})
        up = self._section(scroll, "Обновления", "Проверка новых версий на сервере")
        self.update_status = ctk.CTkLabel(
            up, text=f"Версия {VERSION}", font=T.FONT_SMALL, text_color=T.TEXT_MUTED, anchor="w",
        )
        self.update_status.pack(anchor="w", pady=(0, 4))
        self.auto_update = ctk.BooleanVar(value=upd.get("auto_check", True))
        ctk.CTkCheckBox(
            up, text="Проверять обновления автоматически (раз в 24 ч)",
            variable=self.auto_update, font=T.FONT_SMALL, text_color=T.TEXT_SECONDARY,
            fg_color=self.accent, hover_color=T.DEFAULT_ACCENT_HOVER,
        ).pack(anchor="w")
        self.auto_download = ctk.BooleanVar(value=upd.get("auto_download", True))
        ctk.CTkCheckBox(
            up, text="Скачивать обновление автоматически при обнаружении",
            variable=self.auto_download, font=T.FONT_SMALL, text_color=T.TEXT_SECONDARY,
            fg_color=self.accent, hover_color=T.DEFAULT_ACCENT_HOVER,
        ).pack(anchor="w", pady=(4, 0))
        self._field(
            up, "URL manifest.json (пусто = по умолчанию)", "manifest_url",
            upd.get("manifest_url", ""), placeholder=UPDATE_MANIFEST_URL,
        )
        up_row = ctk.CTkFrame(up, fg_color="transparent")
        up_row.pack(fill="x", pady=(T.PAD_SM, 0))
        ctk.CTkButton(
            up_row, text="Проверить сейчас", width=140, height=32, font=T.FONT_TINY,
            fg_color=T.BG_HOVER, hover_color=T.BORDER, command=self._check_updates,
        ).pack(side="left")

        ab = self._section(scroll, "О программе")
        ctk.CTkLabel(ab, text=f"{PRODUCT_NAME} {PRODUCT_EDITION} · v{VERSION}", font=T.FONT_BODY, text_color=T.TEXT_PRIMARY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(ab, text=COPYRIGHT, font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w", pady=(4, 0))
        ctk.CTkLabel(ab, text=f"EULA v{EULA_VERSION}", font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w", pady=(2, 0))
        ab_row = ctk.CTkFrame(ab, fg_color="transparent")
        ab_row.pack(fill="x", pady=(T.PAD_SM, 0))
        ctk.CTkButton(
            ab_row, text="Документация", width=120, height=32, font=T.FONT_TINY,
            fg_color=T.BG_HOVER, hover_color=T.BORDER,
            command=lambda: show_docs(self.winfo_toplevel()),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            ab_row, text="Сайт", width=80, height=32, font=T.FONT_TINY,
            fg_color=T.BG_HOVER, hover_color=T.BORDER,
            command=lambda: __import__("webbrowser").open(WEBSITE),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            ab_row, text="EULA", width=80, height=32, font=T.FONT_TINY,
            fg_color=T.BG_HOVER, command=lambda: show_eula(self.winfo_toplevel()),
        ).pack(side="left")

    def _build_actions(self):
        self._actions_bar = ctk.CTkFrame(self, fg_color=T.BG_PANEL, corner_radius=T.RADIUS, border_width=1, border_color=T.BORDER)
        self._actions_bar.grid(row=1, column=0, sticky="ew", padx=T.PAD, pady=(0, T.PAD))
        bar = self._actions_bar
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=T.PAD, pady=T.PAD_SM)
        ctk.CTkLabel(inner, text="Сохранить — применить все разделы", font=T.FONT_TINY, text_color=T.TEXT_MUTED).pack(side="left")
        self.save_btn = ctk.CTkButton(
            inner, text="Сохранить настройки", width=180, height=38, font=T.FONT_SMALL,
            fg_color=self.accent, hover_color=T.DEFAULT_ACCENT_HOVER, command=self._save,
        )
        self.save_btn.pack(side="right")

    def _copy_clip(self, text: str):
        self.winfo_toplevel().clipboard_clear()
        self.winfo_toplevel().clipboard_append(text)
        show_toast(self.winfo_toplevel(), "ID ПК скопирован", accent=self.accent)

    def _test_api(self):
        self.ai_picker.set_test_result("Проверка…")

        def worker():
            vals = self.ai_picker.get_values()
            app_config.settings["api_key"] = vals["api_key"]
            app_config.settings["base_url"] = vals["base_url"]
            app_config.settings["model"] = vals["model"]
            app_config.settings["ai_provider"] = vals["ai_provider"]
            from core.ai_client import rp_ai
            ok, msg = rp_ai.test_connection()

            def ui():
                self.ai_picker.set_test_result(msg, ok=ok)

            self.after(0, ui)

        threading.Thread(target=worker, daemon=True).start()

    def _char_by_label(self, label: str) -> dict | None:
        for c in list_characters():
            if c.get("label") == label or c.get("name") == label:
                return c
        return None

    def _load_char_profile_fields(self, label: str):
        c = self._char_by_label(label)
        if not c:
            return
        self._editing_char_id = c.get("id", "")
        self._char_label.delete(0, "end")
        self._char_label.insert(0, c.get("label", ""))
        self._char_name.delete(0, "end")
        self._char_name.insert(0, c.get("name", ""))
        self._char_rank.delete(0, "end")
        self._char_rank.insert(0, c.get("rank", ""))
        self._char_badge.delete(0, "end")
        self._char_badge.insert(0, c.get("badge", ""))
        self._char_personality.delete("0.0", "end")
        self._char_personality.insert("0.0", c.get("personality", ""))

    def _new_char_profile(self):
        n = len(list_characters()) + 1
        entry = save_character({
            "label": f"Персонаж {n}",
            "name": "Новый персонаж",
            "rank": "",
            "badge": "",
            "personality": "",
        })
        labels = [c.get("label", c.get("name", "Персонаж")) for c in list_characters()]
        self._char_profile_box.configure(values=labels)
        self._char_profile_box.set(entry.get("label", labels[-1]))
        self._load_char_profile_fields(entry.get("label", ""))
        show_toast(self.winfo_toplevel(), "Профиль создан", accent=self.accent)

    def _delete_char_profile(self):
        if len(list_characters()) <= 1:
            show_toast(self.winfo_toplevel(), "Нельзя удалить единственный профиль", accent=T.ERROR)
            return
        cid = self._editing_char_id
        if not cid:
            return
        delete_character(cid)
        labels = [c.get("label", c.get("name", "Персонаж")) for c in list_characters()]
        self._char_profile_box.configure(values=labels)
        active = get_active_character()
        self._char_profile_box.set(active.get("label") or labels[0])
        self._load_char_profile_fields(self._char_profile_box.get())
        show_toast(self.winfo_toplevel(), "Профиль удалён", accent=self.accent)

    def reload_from_config(self):
        if hasattr(self, "ai_picker"):
            self.ai_picker.reload()

        active = get_active_character()
        self._editing_char_id = active.get("id", "")
        labels = [c.get("label", c.get("name", "Персонаж")) for c in list_characters()]
        self._char_profile_box.configure(values=labels or ["Основной"])
        self._char_profile_box.set(active.get("label") or (labels[0] if labels else "Основной"))
        for entry, val in (
            (self._char_label, active.get("label", "")),
            (self._char_name, active.get("name", "")),
            (self._char_rank, active.get("rank", "")),
            (self._char_badge, active.get("badge", "")),
        ):
            entry.delete(0, "end")
            entry.insert(0, val)
        self._char_personality.delete("0.0", "end")
        self._char_personality.insert("0.0", active.get("personality", ""))

        self._chat_key.delete(0, "end")
        self._chat_key.insert(0, app_config.get("game", {}).get("chat_key", "t"))

        hk = app_config.get("hotkeys", {})
        self._hotkey_toggle.delete(0, "end")
        self._hotkey_toggle.insert(0, hk.get("toggle_overlay", "shift+\\"))
        self._hotkey_hide.delete(0, "end")
        self._hotkey_hide.insert(0, hk.get("hide_window", "ctrl+shift+h"))
        self._favorites_hotkey.delete(0, "end")
        self._favorites_hotkey.insert(0, hk.get("favorites_overlay", app_config.get("favorites", {}).get("hotkey", "ctrl+alt+f")))

        ui = app_config.get("ui", {})
        self._list_limit.delete(0, "end")
        self._list_limit.insert(0, str(ui.get("list_limit", 120)))
        self.auto_ai.set(ui.get("auto_send_ai", False))
        self.ui_animations.set(bool(ui.get("animations", False)))
        if hasattr(self, "theme_picker"):
            self.theme_picker.reload()

        sr = app_config.get("search", {})
        self.wikipedia_search.set(sr.get("wikipedia", True))
        self.online_fallback.set(sr.get("online_fallback", True))
        self.rag_search.set(sr.get("rag", True))

        lic = app_config.get("license", {})
        self.license_status.configure(
            text=license_status_text(lic),
            text_color=T.SUCCESS if is_licensed(lic) else T.TEXT_MUTED,
        )
        self._license_key.delete(0, "end")

        u = app_config.get("updates", {})
        self.auto_update.set(u.get("auto_check", True))
        self.auto_download.set(u.get("auto_download", True))
        self._manifest_url.delete(0, "end")
        self._manifest_url.insert(0, u.get("manifest_url", ""))

    def set_update_status(self, text: str, *, ok: bool = True):
        self.update_status.configure(text=text, text_color=T.SUCCESS if ok else T.TEXT_MUTED)

    def _check_updates(self):
        if self.on_check_updates:
            self.update_status.configure(text="Проверка обновлений…", text_color=T.TEXT_MUTED)
            self.on_check_updates(force=True)

    def _save_license(self) -> bool:
        key = self._license_key.get().strip()
        if not key:
            return True
        if not validate_license_key(key):
            hint = license_key_error_hint(key)
            show_toast(
                self.winfo_toplevel(),
                hint or "Неверный ключ или не подходит к этому ПК",
                accent=T.ERROR,
            )
            return False
        try:
            app_config.set("license", activate_license(key))
        except ValueError:
            show_toast(self.winfo_toplevel(), "Ошибка активации", accent=T.ERROR)
            return False
        self.license_status.configure(text=license_status_text(app_config.get("license")), text_color=T.SUCCESS)
        self._license_key.delete(0, "end")
        return True

    def _save(self):
        ai_vals = self.ai_picker.get_values()
        app_config.set("api_key", ai_vals["api_key"])
        app_config.set("base_url", ai_vals["base_url"])
        app_config.set("model", ai_vals["model"] or "gpt-4o-mini")
        app_config.set("ai_provider", ai_vals["ai_provider"])
        entry = save_character({
            "id": self._editing_char_id,
            "label": self._char_label.get().strip() or self._char_name.get().strip() or "Персонаж",
            "name": self._char_name.get().strip(),
            "rank": self._char_rank.get().strip(),
            "badge": self._char_badge.get().strip(),
            "personality": self._char_personality.get("0.0", "end").strip(),
        })
        set_active_character(entry["id"])
        app_config.set("game", {"chat_key": self._chat_key.get().strip() or "t"})
        try:
            limit = max(40, min(500, int(self._list_limit.get().strip() or "120")))
        except ValueError:
            limit = 120
        theme_vals = self.theme_picker.get_values() if hasattr(self, "theme_picker") else {}
        app_config.set("ui", {
            "list_limit": limit,
            "auto_send_ai": bool(self.auto_ai.get()),
            "animations": bool(self.ui_animations.get()),
            "theme": theme_vals.get("theme", app_config.get("ui", {}).get("theme", "helperp")),
            "use_faction_accent": theme_vals.get("use_faction_accent", True),
            "custom_accent": theme_vals.get("custom_accent", ""),
        })
        app_config.set("search", {
            "wikipedia": bool(self.wikipedia_search.get()),
            "online_fallback": bool(self.online_fallback.get()),
            "rag": bool(self.rag_search.get()),
        })
        discord_cfg = app_config.get("discord", {}) or {}
        app_config.set("discord", {
            "enabled": bool(self.discord_enabled.get()),
            "client_id": self._discord_client_id.get().strip(),
            "details": self._discord_details.get().strip() or "HelpeRP — база знаний",
            "state": self._discord_state.get().strip() or "Режим поиска и подготовки RP",
            "button_label": self._discord_button_label.get().strip() or "Открыть HelpeRP",
            "button_url": self._discord_button_url.get().strip() or "https://yeolka-lm.github.io/HelpeRP_Client/",
        })
        favorites_cfg = app_config.get("favorites", {}) or {}
        app_config.set("favorites", {
            "items": favorites_cfg.get("items", []),
            "hotkey": self._favorites_hotkey.get().strip() or "ctrl+alt+f",
            "mode": favorites_cfg.get("mode", "compact"),
            "max_items": max(1, int(favorites_cfg.get("max_items", 8) or 8)),
        })
        app_config.set("hotkeys", {
            "toggle_overlay": self._hotkey_toggle.get().strip() or "shift+\\",
            "hide_window": self._hotkey_hide.get().strip() or "ctrl+shift+h",
            "favorites_overlay": self._favorites_hotkey.get().strip() or "ctrl+alt+f",
            "submit_request": app_config.get("hotkeys", {}).get("submit_request", "enter"),
        })
        app_config.set("updates", {
            "auto_check": bool(self.auto_update.get()),
            "auto_download": bool(self.auto_download.get()),
            "check_interval_hours": app_config.get("updates", {}).get("check_interval_hours", 24),
            "last_check": app_config.get("updates", {}).get("last_check"),
            "dismissed_version": app_config.get("updates", {}).get("dismissed_version", ""),
            "manifest_url": self._manifest_url.get().strip(),
        })
        if not self._save_license():
            return
        if self.on_saved:
            self.on_saved()
        show_toast(self.winfo_toplevel(), "Настройки сохранены", accent=self.accent)
