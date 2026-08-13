"""Диалог уведомления и автоматической установки обновления."""

from __future__ import annotations

import threading
import webbrowser
from pathlib import Path

import customtkinter as ctk

from core.update_installer import (
    UpdateInstallError,
    cached_update_path,
    can_auto_install,
    download_update,
    install_update,
)
from core.updates import UpdateInfo, dismiss_version
from core.version import PRODUCT_NAME
from gui import theme as T
from gui.animations import ANIM_NORMAL, Animator, animations_enabled
from gui.toast import show_toast


class UpdateDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        info: UpdateInfo,
        *,
        package_path: Path | None = None,
        on_dismiss=None,
        accent: str = T.DEFAULT_ACCENT,
    ):
        super().__init__(parent)
        self.info = info
        self.on_dismiss = on_dismiss
        self.accent = accent
        self._package_path = package_path or cached_update_path(info)
        self._busy = False

        self.title(f"{PRODUCT_NAME} — обновление")
        self.configure(fg_color=T.BG_ROOT)
        self.geometry("520x500")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        if animations_enabled():
            try:
                self.attributes("-alpha", 0.0)
                self.after(30, lambda: Animator.fade_window(self, 0.0, 1.0, ANIM_NORMAL))
            except Exception:
                pass

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=T.PAD, pady=(T.PAD, T.PAD_SM))
        ctk.CTkLabel(hdr, text="Доступно обновление", font=T.FONT_HEADING, text_color=T.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(
            hdr,
            text=f"Текущая: v{info.current}  →  Новая: v{info.latest}",
            font=T.FONT_SMALL,
            text_color=T.SUCCESS,
        ).pack(anchor="w", pady=(4, 0))
        if info.released:
            ctk.CTkLabel(hdr, text=f"Дата релиза: {info.released}", font=T.FONT_TINY, text_color=T.TEXT_MUTED).pack(anchor="w")

        ctk.CTkLabel(self, text=info.title, font=T.FONT_BODY, text_color=T.TEXT_PRIMARY, anchor="w").pack(
            anchor="w", padx=T.PAD,
        )

        box = ctk.CTkTextbox(
            self, font=T.FONT_SMALL, fg_color=T.BG_PANEL, border_width=1, border_color=T.BORDER, wrap="word",
        )
        box.pack(fill="both", expand=True, padx=T.PAD, pady=T.PAD_SM)
        box.insert("0.0", info.changelog)
        box.configure(state="disabled")

        self.status_label = ctk.CTkLabel(
            self, text="", font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w",
        )
        self.status_label.pack(fill="x", padx=T.PAD)

        self.progress = ctk.CTkProgressBar(self, height=8)
        self.progress.pack(fill="x", padx=T.PAD, pady=(4, T.PAD_SM))
        self.progress.set(0)
        if self._package_path:
            self.progress.set(1)
            self.status_label.configure(text="Пакет уже загружен — можно установить", text_color=T.SUCCESS)

        if info.required:
            ctk.CTkLabel(
                self, text="Рекомендуется обновиться для продолжения работы.",
                font=T.FONT_TINY, text_color=T.WARNING,
            ).pack(anchor="w", padx=T.PAD)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=T.PAD, pady=(0, T.PAD))

        ctk.CTkButton(
            actions, text="Позже", width=90, fg_color=T.BG_HOVER, hover_color=T.BORDER, command=self.destroy,
        ).pack(side="left")
        ctk.CTkButton(
            actions, text="Пропустить версию", width=130, fg_color=T.BG_HOVER, hover_color=T.BORDER,
            command=self._skip,
        ).pack(side="left", padx=(8, 0))

        self.browser_btn = ctk.CTkButton(
            actions, text="В браузере", width=100, fg_color=T.BG_HOVER, hover_color=T.BORDER,
            command=self._download_browser,
        )
        self.browser_btn.pack(side="right", padx=(8, 0))

        self.install_btn = ctk.CTkButton(
            actions, text="Установить автоматически", width=180,
            fg_color=self.accent, hover_color=T.DEFAULT_ACCENT_HOVER,
            command=self._install,
        )
        self.install_btn.pack(side="right")

        if not can_auto_install():
            self.install_btn.configure(state="disabled")
            self.status_label.configure(
                text="Автоустановка доступна в собранном HelpeRP.exe",
                text_color=T.TEXT_MUTED,
            )
        elif not self._package_path and info.download_url:
            self.after(200, self._start_download)

    def _set_busy(self, busy: bool, status: str = ""):
        self._busy = busy
        state = "disabled" if busy else "normal"
        self.install_btn.configure(state=state if can_auto_install() else "disabled")
        self.browser_btn.configure(state=state)
        if status:
            self.status_label.configure(text=status)

    def _progress(self, done: int, total: int):
        pct = 1.0 if total <= 0 else min(1.0, done / total)
        self.progress.set(pct)
        if total > 0:
            mb_done = done / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.status_label.configure(text=f"Загрузка… {mb_done:.1f} / {mb_total:.1f} МБ")

    def _start_download(self):
        if self._busy or self._package_path:
            return
        self._set_busy(True, "Загрузка обновления…")

        def worker():
            try:
                path = download_update(self.info, progress=lambda d, t: self.after(0, lambda: self._progress(d, t)))
                self.after(0, lambda: self._on_download_done(path))
            except UpdateInstallError as e:
                self.after(0, lambda: self._on_download_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_download_done(self, path: Path):
        self._package_path = path
        self._set_busy(False)
        self.progress.set(1)
        self.status_label.configure(text="Загрузка завершена — нажмите «Установить»", text_color=T.SUCCESS)

    def _on_download_error(self, message: str):
        self._set_busy(False)
        self.status_label.configure(text=message, text_color=T.ERROR)

    def _install(self):
        if not self._package_path:
            self._start_download()
            return
        self._set_busy(True, "Подготовка установки…")

        def worker():
            try:
                install_update(self._package_path)
            except UpdateInstallError as e:
                self.after(0, lambda: self._on_download_error(str(e)))
                self.after(0, lambda: self._set_busy(False))

        threading.Thread(target=worker, daemon=True).start()

    def _skip(self):
        dismiss_version(self.info.latest)
        if self.on_dismiss:
            self.on_dismiss()
        self.destroy()

    def _download_browser(self):
        if self.info.download_url:
            webbrowser.open(self.info.download_url)
        self.destroy()


def show_update_dialog(parent, info: UpdateInfo, *, package_path: Path | None = None, on_dismiss=None, accent: str = T.DEFAULT_ACCENT):
    UpdateDialog(parent, info, package_path=package_path, on_dismiss=on_dismiss, accent=accent)
