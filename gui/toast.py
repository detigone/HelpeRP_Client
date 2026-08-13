"""Всплывающие уведомления с анимацией."""

import customtkinter as ctk

from gui import theme as T
from gui.animations import ANIM_NORMAL, Animator, animations_enabled


def show_toast(root, message: str, duration_ms: int = 2400, accent: str | None = None):
    toast = ctk.CTkFrame(
        root,
        fg_color=T.BG_CARD,
        corner_radius=T.RADIUS_SM,
        border_width=1,
        border_color=accent or T.BORDER_LIGHT,
    )
    label = ctk.CTkLabel(
        toast, text=message, font=T.FONT_SMALL, text_color=T.TEXT_PRIMARY,
        padx=16, pady=8,
    )
    label.pack()

    if animations_enabled():
        toast.place(relx=0.5, rely=1.08, anchor="s")
        Animator.slide_in_place(toast, root, start_rely=1.08, end_rely=0.97, duration=ANIM_NORMAL)
    else:
        toast.place(relx=0.5, rely=0.97, anchor="s")

    def hide():
        if not toast.winfo_exists():
            return
        if animations_enabled():
            Animator.slide_out_place(
                toast, root, end_rely=1.08, on_done=lambda: _destroy(toast),
            )
        else:
            _destroy(toast)

    root.after(duration_ms, hide)


def _destroy(widget):
    try:
        widget.destroy()
    except Exception:
        pass
