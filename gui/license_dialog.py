"""Диалог принятия EULA и активации лицензии."""

import customtkinter as ctk

from core.config import app_config
from core.licensing import activate_license, get_machine_code_display, is_dev_mode, license_key_error_hint, validate_license_key
from core.version import COPYRIGHT, EULA_VERSION, PRODUCT_NAME, PURCHASE_URL, SUPPORT_EMAIL, VERSION
from gui import theme as T
from gui.eula_dialog import show_eula, load_eula_text


class LicenseDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_activated=None):
        super().__init__(parent)
        self.on_activated = on_activated
        self.title(f"{PRODUCT_NAME} — активация")
        self.configure(fg_color=T.BG_ROOT)
        self.geometry("580x680")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=T.PAD, pady=(T.PAD, T.PAD_SM))
        ctk.CTkLabel(header, text=f"{PRODUCT_NAME} v{VERSION}", font=T.FONT_HEADING, text_color=T.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(
            header, text="Коммерческая лицензия · один ключ — одна установка",
            font=T.FONT_TINY, text_color=T.TEXT_MUTED,
        ).pack(anchor="w", pady=(4, 0))

        eula_hdr = ctk.CTkFrame(self, fg_color="transparent")
        eula_hdr.pack(fill="x", padx=T.PAD)
        ctk.CTkLabel(eula_hdr, text="EULA", font=T.FONT_TINY, text_color=T.TEXT_MUTED).pack(side="left")
        ctk.CTkButton(
            eula_hdr, text="Открыть полностью", width=130, height=24, font=T.FONT_TINY,
            fg_color=T.BG_HOVER, hover_color=T.BORDER,
            command=lambda: show_eula(self),
        ).pack(side="right")

        preview = ctk.CTkTextbox(self, height=200, font=T.FONT_TINY, fg_color=T.BG_PANEL, border_width=1, border_color=T.BORDER, wrap="word")
        preview.pack(fill="x", padx=T.PAD, pady=(4, T.PAD_SM))
        text = load_eula_text()
        preview.insert("0.0", text[:2200] + ("\n\n…" if len(text) > 2200 else ""))
        preview.configure(state="disabled")

        self.accept_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self, text=f"Принимаю лицензионное соглашение (v{EULA_VERSION})",
            variable=self.accept_var, font=T.FONT_SMALL, text_color=T.TEXT_SECONDARY,
        ).pack(anchor="w", padx=T.PAD, pady=(0, T.PAD_SM))

        key_frame = ctk.CTkFrame(self, fg_color=T.BG_PANEL, corner_radius=T.RADIUS)
        key_frame.pack(fill="x", padx=T.PAD, pady=(0, T.PAD_SM))
        inner = ctk.CTkFrame(key_frame, fg_color="transparent")
        inner.pack(fill="x", padx=T.PAD, pady=T.PAD_SM)

        ctk.CTkLabel(inner, text="Лицензионный ключ", font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w")
        key_row = ctk.CTkFrame(inner, fg_color="transparent")
        key_row.pack(fill="x", pady=(4, 4))
        key_row.grid_columnconfigure(0, weight=1)
        self.key_entry = ctk.CTkEntry(
            key_row, placeholder_text="HELPE-XXXX-XXXX-XXXXXXXX", height=38,
            font=T.FONT_BODY, fg_color=T.BG_INPUT, border_color=T.BORDER,
        )
        self.key_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(
            key_row, text="Вставить", width=90, height=38, font=T.FONT_TINY,
            fg_color=T.BG_HOVER, hover_color=T.BORDER, command=self._paste_key,
        ).grid(row=0, column=1)
        ctk.CTkLabel(
            inner, text="Ctrl+V — вставить · Enter — активировать",
            font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w",
        ).pack(anchor="w", pady=(0, 4))

        mc = get_machine_code_display()
        mc_row = ctk.CTkFrame(inner, fg_color="transparent")
        mc_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(mc_row, text=f"ID этого ПК: {mc}", font=T.FONT_TINY, text_color=T.TEXT_SECONDARY, anchor="w").pack(side="left")
        ctk.CTkButton(
            mc_row, text="Копировать", width=90, height=24, font=T.FONT_TINY,
            fg_color=T.BG_HOVER, command=lambda: self._copy(mc),
        ).pack(side="right")
        ctk.CTkLabel(
            inner, text="Для ключа с привязкой к ПК отправьте этот ID продавцу",
            font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w",
        ).pack(anchor="w")

        if is_dev_mode():
            ctk.CTkLabel(inner, text="Режим разработки: ключ не требуется", font=T.FONT_TINY, text_color=T.WARNING).pack(anchor="w", pady=(4, 0))

        self.error_label = ctk.CTkLabel(inner, text="", font=T.FONT_TINY, text_color=T.ERROR)
        self.error_label.pack(anchor="w")

        ctk.CTkLabel(
            inner, text=f"Покупка: {PURCHASE_URL}  ·  {SUPPORT_EMAIL}",
            font=T.FONT_TINY, text_color=T.TEXT_MUTED, wraplength=520, justify="left",
        ).pack(anchor="w", pady=(6, 0))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=T.PAD, pady=(0, T.PAD_SM))
        ctk.CTkButton(actions, text="Выход", width=100, fg_color=T.BG_HOVER, hover_color=T.BORDER, command=self._on_close).pack(side="left")
        ctk.CTkButton(
            actions, text="Активировать", width=140,
            fg_color=T.DEFAULT_ACCENT, hover_color=T.DEFAULT_ACCENT_HOVER, command=self._activate,
        ).pack(side="right")

        ctk.CTkLabel(self, text=COPYRIGHT, font=T.FONT_TINY, text_color=T.TEXT_MUTED).pack(pady=(0, T.PAD))

        self.key_entry.bind("<Return>", lambda e: self._activate())
        self.after(150, self.key_entry.focus_set)

    def _paste_key(self):
        try:
            text = self.clipboard_get().strip()
        except Exception:
            self.error_label.configure(text="Буфер обмена пуст или недоступен.")
            return
        if not text:
            self.error_label.configure(text="Буфер обмена пуст.")
            return
        self.key_entry.delete(0, "end")
        self.key_entry.insert(0, text.upper().replace(" ", ""))
        self.error_label.configure(text="")

    def _copy(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)

    def _on_close(self):
        self.destroy()
        self.master.destroy()

    def _activate(self):
        if not self.accept_var.get():
            self.error_label.configure(text="Примите EULA для продолжения.")
            return

        key = self.key_entry.get().strip()
        if is_dev_mode() and not key:
            app_config.set("license", activate_license(""))
            if self.on_activated:
                self.on_activated()
            self.destroy()
            return

        if not key:
            self.error_label.configure(text="Введите лицензионный ключ.")
            return
        if not validate_license_key(key):
            hint = license_key_error_hint(key)
            self.error_label.configure(
                text=hint or "Неверный ключ или не подходит к этому ПК.",
            )
            return

        try:
            app_config.set("license", activate_license(key))
        except ValueError:
            self.error_label.configure(text="Ключ не прошёл проверку.")
            return

        if self.on_activated:
            self.on_activated()
        self.destroy()
