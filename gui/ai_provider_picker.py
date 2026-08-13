"""Выбор AI-провайдера и модели."""

from __future__ import annotations

import threading

import customtkinter as ctk

from core.ai_providers import (
    PROVIDER_LABELS,
    PROVIDERS,
    detect_provider,
    provider_defaults,
    provider_id_by_label,
    provider_label,
)
from core.config import app_config
from core.local_ai import fetch_local_models, is_local_provider
from gui import theme as T


class AIProviderPicker(ctk.CTkFrame):
    def __init__(self, master, accent: str = T.DEFAULT_ACCENT, on_test=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.accent = accent
        self.on_test = on_test
        self._fetching = False

        pid = app_config.get("ai_provider") or detect_provider(app_config.get("base_url", ""))
        label = provider_label(pid)

        ctk.CTkLabel(
            self, text="Провайдер", font=T.FONT_TINY, text_color=T.TEXT_SECONDARY, anchor="w",
        ).pack(fill="x", pady=(0, 2))
        self.provider_box = ctk.CTkComboBox(
            self, values=PROVIDER_LABELS, height=36, font=T.FONT_SMALL,
            fg_color=T.BG_INPUT, border_color=T.BORDER, command=self._on_provider,
        )
        self.provider_box.pack(fill="x")
        self.provider_box.set(label if label in PROVIDER_LABELS else PROVIDER_LABELS[0])

        model_row = ctk.CTkFrame(self, fg_color="transparent")
        model_row.pack(fill="x", pady=(T.PAD_SM, 0))
        model_col = ctk.CTkFrame(model_row, fg_color="transparent")
        model_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            model_col, text="Модель", font=T.FONT_TINY, text_color=T.TEXT_SECONDARY, anchor="w",
        ).pack(fill="x", pady=(0, 2))
        self.model_box = ctk.CTkComboBox(
            model_col, values=[], height=36, font=T.FONT_SMALL,
            fg_color=T.BG_INPUT, border_color=T.BORDER,
        )
        self.model_box.pack(fill="x")

        self.refresh_models_btn = ctk.CTkButton(
            model_row, text="↻", width=36, height=36, font=T.FONT_BODY,
            fg_color=T.BG_HOVER, hover_color=T.BORDER, command=self._fetch_local_models,
        )
        self.refresh_models_btn.pack(side="right", padx=(8, 0), pady=(18, 0))

        self.api_key_label = ctk.CTkLabel(
            self, text="API-ключ", font=T.FONT_TINY, text_color=T.TEXT_SECONDARY, anchor="w",
        )
        self.api_key_label.pack(fill="x", pady=(T.PAD_SM, 2))
        self.api_key = ctk.CTkEntry(
            self, height=36, font=T.FONT_SMALL, fg_color=T.BG_INPUT, border_color=T.BORDER, show="•",
        )
        self.api_key.pack(fill="x")
        self.api_key.insert(0, app_config.get("api_key", ""))

        ctk.CTkLabel(
            self, text="Base URL (OpenAI-совместимый)", font=T.FONT_TINY, text_color=T.TEXT_SECONDARY, anchor="w",
        ).pack(fill="x", pady=(T.PAD_SM, 2))
        self.base_url = ctk.CTkEntry(
            self, height=36, font=T.FONT_SMALL, fg_color=T.BG_INPUT, border_color=T.BORDER,
            placeholder_text="http://localhost:11434/v1",
        )
        self.base_url.pack(fill="x")
        self.base_url.insert(0, app_config.get("base_url", ""))

        self.local_badge = ctk.CTkLabel(
            self, text="", font=T.FONT_TINY, text_color=T.SUCCESS, anchor="w",
        )
        self.local_badge.pack(fill="x", pady=(T.PAD_SM, 0))

        self.hint_label = ctk.CTkLabel(
            self, text="", font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w", justify="left",
        )
        self.hint_label.pack(fill="x", pady=(4, 0))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", pady=(T.PAD_SM, 0))
        self.test_label = ctk.CTkLabel(row, text="", font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w")
        self.test_label.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            row, text="Проверить API", width=120, height=32, font=T.FONT_TINY,
            fg_color=T.BG_HOVER, hover_color=T.BORDER, command=self._run_test,
        ).pack(side="right")

        self._sync_models(initial=True)
        self._update_local_ui()

    def _current_provider_id(self) -> str:
        return provider_id_by_label(self.provider_box.get())

    def _on_provider(self, _=None):
        pid = self._current_provider_id()
        defaults = provider_defaults(pid)
        if pid != "custom":
            self.base_url.delete(0, "end")
            self.base_url.insert(0, defaults["base_url"])
        p = PROVIDERS[pid]
        self.api_key.configure(placeholder_text=p.get("key_hint", ""))
        self._sync_models(reset_model=True)
        self._update_local_ui()
        if is_local_provider(pid):
            self._fetch_local_models()

    def _update_local_ui(self):
        pid = self._current_provider_id()
        local = is_local_provider(pid)
        if local:
            self.local_badge.configure(
                text="Локальный режим — данные не уходят в облако, сервер не нужен",
            )
            self.api_key_label.configure(text="API-ключ (для локальных не нужен)")
            self.refresh_models_btn.configure(state="normal")
        else:
            self.local_badge.configure(text="")
            self.api_key_label.configure(text="API-ключ")
            self.refresh_models_btn.configure(state="disabled")
        self._update_hint()

    def _sync_models(self, *, reset_model: bool = False, initial: bool = False, extra: list[str] | None = None):
        pid = self._current_provider_id()
        defaults = provider_defaults(pid)
        models = list(extra or defaults["models"] or [])
        if defaults["model"] and defaults["model"] not in models:
            models.insert(0, defaults["model"])
        saved = app_config.get("model", "")
        if models:
            self.model_box.configure(values=models)
            if initial and saved:
                self.model_box.set(saved if saved in models else models[0])
            elif reset_model:
                self.model_box.set(defaults["model"] or models[0])
            elif self.model_box.get() not in models:
                self.model_box.set(models[0])
        else:
            self.model_box.configure(values=[saved] if saved else [""])
            if reset_model and not saved:
                self.model_box.set("")
            elif initial or saved:
                self.model_box.set(saved)
        self._update_hint()

    def _fetch_local_models(self):
        pid = self._current_provider_id()
        if not is_local_provider(pid) or self._fetching:
            return
        self._fetching = True
        self.refresh_models_btn.configure(state="disabled")
        self.test_label.configure(text="Загрузка моделей…", text_color=T.TEXT_MUTED)
        base = self.base_url.get().strip()
        key = self.api_key.get().strip()

        def worker():
            models, err = fetch_local_models(pid, base, key)

            def ui():
                self._fetching = False
                self.refresh_models_btn.configure(state="normal")
                if models:
                    current = self.model_box.get().strip()
                    self._sync_models(extra=models)
                    if current in models:
                        self.model_box.set(current)
                    self.test_label.configure(
                        text=f"Найдено моделей: {len(models)}", text_color=T.SUCCESS,
                    )
                elif err:
                    self.test_label.configure(text=err, text_color=T.ERROR)

            self.after(0, ui)

        threading.Thread(target=worker, daemon=True).start()

    def _update_hint(self):
        pid = self._current_provider_id()
        p = PROVIDERS.get(pid, PROVIDERS["custom"])
        if pid == "custom":
            text = "Укажите Base URL и модель OpenAI-совместимого сервера (можно локальный)."
        elif is_local_provider(pid):
            text = p.get("setup", "Запустите локальный сервер на своём ПК.")
        else:
            text = f"Облачный API · ключ: {p.get('key_hint', '…')}"
        docs = p.get("docs", "")
        if docs:
            text += f"  ·  {docs}"
        self.hint_label.configure(text=text)

    def _run_test(self):
        if self.on_test:
            self.on_test()

    def set_test_result(self, text: str, *, ok: bool = False):
        self.test_label.configure(text=text, text_color=T.SUCCESS if ok else T.ERROR if text else T.TEXT_MUTED)

    def get_values(self) -> dict:
        return {
            "ai_provider": self._current_provider_id(),
            "api_key": self.api_key.get().strip(),
            "base_url": self.base_url.get().strip(),
            "model": self.model_box.get().strip(),
        }

    def reload(self):
        pid = app_config.get("ai_provider") or detect_provider(app_config.get("base_url", ""))
        label = provider_label(pid)
        self.provider_box.set(label if label in PROVIDER_LABELS else PROVIDER_LABELS[0])
        self.api_key.delete(0, "end")
        self.api_key.insert(0, app_config.get("api_key", ""))
        self.base_url.delete(0, "end")
        self.base_url.insert(0, app_config.get("base_url", ""))
        self.test_label.configure(text="", text_color=T.TEXT_MUTED)
        self._sync_models(initial=True)
        self._update_local_ui()
        if is_local_provider(pid):
            self._fetch_local_models()

    def set_accent(self, color: str):
        self.accent = color

    def apply_theme(self):
        self.provider_box.configure(fg_color=T.BG_INPUT, border_color=T.BORDER)
        self.model_box.configure(fg_color=T.BG_INPUT, border_color=T.BORDER)
        self.api_key.configure(fg_color=T.BG_INPUT, border_color=T.BORDER)
        self.base_url.configure(fg_color=T.BG_INPUT, border_color=T.BORDER)
