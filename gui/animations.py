"""Плавные UI-анимации HelpeRP."""

from __future__ import annotations

import re

import customtkinter as ctk

from gui import theme as T

FPS = 60
ANIM_FAST = 140
ANIM_NORMAL = 240
ANIM_SLOW = 380


def animations_enabled() -> bool:
    try:
        from core.config import app_config
        return bool(app_config.get("ui", {}).get("animations", True))
    except Exception:
        return True


def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def ease_in_out_quad(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2


def _parse_hex(color: str) -> tuple[int, int, int]:
    color = (color or "#000000").lstrip("#")
    if len(color) == 3:
        color = "".join(c * 2 for c in color)
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def lerp_color(c1: str, c2: str, t: float) -> str:
    t = ease_out_cubic(t)
    r1, g1, b1 = _parse_hex(c1)
    r2, g2, b2 = _parse_hex(c2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def parse_geometry(geo: str) -> tuple[int, int, int, int]:
    m = re.match(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", geo or "")
    if not m:
        return 800, 600, 100, 100
    return int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))


class Animator:
    _tokens: dict[int, int] = {}

    @classmethod
    def cancel(cls, widget) -> None:
        wid = id(widget)
        job = cls._tokens.pop(wid, None)
        if job is not None:
            try:
                widget.after_cancel(job)
            except Exception:
                pass

    @classmethod
    def tween(cls, widget, duration_ms: int, on_frame, *, on_done=None, easing=ease_out_cubic):
        cls.cancel(widget)
        steps = max(1, int(duration_ms / (1000 / FPS)))

        state = {"step": 0}

        def tick():
            state["step"] += 1
            t = min(1.0, state["step"] / steps)
            try:
                on_frame(easing(t), t)
            except Exception:
                cls._tokens.pop(id(widget), None)
                return
            if state["step"] < steps:
                cls._tokens[id(widget)] = widget.after(int(1000 / FPS), tick)
            else:
                cls._tokens.pop(id(widget), None)
                if on_done:
                    on_done()

        tick()

    @classmethod
    def fade_window(cls, root, start: float, end: float, duration: int = ANIM_NORMAL, *, on_done=None):
        try:
            root.attributes("-alpha", start)
        except Exception:
            if on_done:
                on_done()
            return

        def frame(t, _):
            try:
                root.attributes("-alpha", start + (end - start) * t)
            except Exception:
                pass

        cls.tween(root, duration, frame, on_done=on_done)

    @classmethod
    def animate_geometry(
        cls,
        root,
        target_w: int,
        target_h: int,
        *,
        duration: int = ANIM_NORMAL,
        on_mid=None,
        on_done=None,
    ):
        w, h, x, y = parse_geometry(root.geometry())
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        mid_called = {"ok": False}

        def frame(t, _):
            nonlocal x, y
            cw = int(w + (target_w - w) * t)
            ch = int(h + (target_h - h) * t)
            nx = (sw - cw) // 2
            ny = 12 if target_h <= 80 else (sh - ch) // 2
            root.geometry(f"{cw}x{ch}+{nx}+{ny}")
            if on_mid and t >= 0.48 and not mid_called["ok"]:
                mid_called["ok"] = True
                on_mid()

        cls.tween(root, duration, frame, on_done=on_done)

    @classmethod
    def color_pulse(cls, widget, root, base: str, peak: str, *, duration: int = ANIM_NORMAL, cycles: int = 1, on_done=None):
        total = duration * cycles

        def frame(t, _):
            wave = abs((t * cycles * 2) % 2 - 1)
            try:
                widget.configure(fg_color=lerp_color(base, peak, wave))
            except Exception:
                pass

        cls.tween(root, total, frame, on_done=on_done)

    @classmethod
    def flash_bar(cls, bar, root, accent: str, *, height: int = 3):
        if not animations_enabled():
            return

        def frame(t, _):
            h = height + int(5 * (1 - abs(t * 2 - 1)))
            try:
                bar.configure(height=h, fg_color=lerp_color(accent, T.TEXT_PRIMARY, t * 0.35))
            except Exception:
                pass

        def restore():
            try:
                bar.configure(height=height, fg_color=accent)
            except Exception:
                pass

        cls.tween(root, ANIM_FAST, frame, on_done=restore)

    @classmethod
    def stagger_buttons(
        cls,
        root,
        buttons: list,
        *,
        target_color: str = T.BG_CARD,
        hidden_color: str = T.BG_ROOT,
        delay: int = 24,
        max_items: int = 40,
    ):
        if not animations_enabled() or not buttons:
            return
        for i, btn in enumerate(buttons[:max_items]):
            try:
                btn.configure(fg_color=hidden_color)
            except Exception:
                continue

            def reveal(b=btn, step=i):
                Animator.tween(
                    root,
                    ANIM_FAST,
                    lambda t, _: b.configure(fg_color=lerp_color(hidden_color, target_color, t)),
                )

            root.after(i * delay, reveal)

    @classmethod
    def highlight_button(cls, btn, root, accent: str, *, base: str = T.BG_CARD):
        if not animations_enabled():
            btn.configure(fg_color=T.BG_SELECTED, border_width=2, border_color=accent)
            return

        def frame(t, _):
            btn.configure(
                fg_color=lerp_color(base, T.BG_SELECTED, t),
                border_width=2 if t > 0.4 else 0,
                border_color=lerp_color(base, accent, t),
            )

        cls.tween(root, ANIM_FAST, frame)

    @classmethod
    def slide_in_place(cls, widget, root, *, start_rely: float = 1.02, end_rely: float = 0.97, duration: int = ANIM_NORMAL, on_done=None):
        widget.place(relx=0.5, rely=start_rely, anchor="s")

        def frame(t, _):
            rely = start_rely + (end_rely - start_rely) * t
            widget.place(relx=0.5, rely=rely, anchor="s")

        cls.tween(root, duration, frame, on_done=on_done)

    @classmethod
    def slide_out_place(cls, widget, root, *, end_rely: float = 1.06, duration: int = ANIM_FAST, on_done=None):
        try:
            info = widget.place_info()
            start = float(info.get("rely", "0.97"))
        except Exception:
            start = 0.97

        def frame(t, _):
            rely = start + (end_rely - start) * t
            widget.place(relx=0.5, rely=rely, anchor="s")

        cls.tween(root, duration, frame, on_done=on_done)


class LoadingDots:
    """Анимированный индикатор загрузки."""

    FRAMES = ("●○○", "○●○", "○○●", "○●○")

    def __init__(self, label: ctk.CTkLabel):
        self.label = label
        self._job = None
        self._i = 0
        self._base = ""

    def start(self, base_text: str = "Загрузка"):
        self.stop()
        self._base = base_text
        self._tick()

    def stop(self, final_text: str = ""):
        if self._job:
            try:
                self.label.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        if final_text:
            try:
                self.label.configure(text=final_text)
            except Exception:
                pass

    def _tick(self):
        if not animations_enabled():
            self.label.configure(text=self._base)
            return
        frame = self.FRAMES[self._i % len(self.FRAMES)]
        self._i += 1
        try:
            self.label.configure(text=f"{self._base}  {frame}")
        except Exception:
            return
        self._job = self.label.after(280, self._tick)


class PulseBadge:
    """Мягкая пульсация кнопки-бейджа."""

    def __init__(self, button: ctk.CTkButton, root, accent: str = T.WARNING):
        self.button = button
        self.root = root
        self.accent = accent
        self._job = None
        self._on = False

    def start(self):
        self.stop()
        if not animations_enabled():
            return
        self._on = True
        self._pulse(0)

    def stop(self):
        self._on = False
        if self._job:
            try:
                self.root.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

    def _pulse(self, step: int):
        if not self._on:
            return
        t = (step % 30) / 30
        wave = 0.35 + 0.65 * abs((t * 2) % 2 - 1)
        color = lerp_color(T.BG_HOVER, self.accent, wave)
        try:
            self.button.configure(text_color=color, fg_color=lerp_color(T.BG_HOVER, T.BG_CARD, wave * 0.4))
        except Exception:
            return
        self._job = self.root.after(50, lambda: self._pulse(step + 1))
