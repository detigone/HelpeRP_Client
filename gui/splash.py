"""Splash screen shown during startup."""

import customtkinter as ctk
import threading
import time
from gui import theme as T
from gui.icons import ui_icon


class SplashScreen:
    def __init__(self, on_ready_callback):
        self.on_ready_callback = on_ready_callback
        self.root = ctk.CTk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        w, h = 420, 240
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        
        self.root.configure(fg_color=T.BG_ROOT)
        
        main_frame = ctk.CTkFrame(self.root, fg_color=T.BG_SIDEBAR, corner_radius=T.RADIUS, 
                                   border_width=1, border_color=T.BORDER)
        main_frame.pack(fill="both", expand=True, padx=16, pady=16)
        
        logo = ui_icon("app", 64)
        if logo:
            ctk.CTkLabel(main_frame, text="", image=logo).pack(pady=(24, 8))
        
        ctk.CTkLabel(main_frame, text="HelpeRP", font=T.FONT_TITLE, 
                     text_color=T.TEXT_PRIMARY).pack()
        ctk.CTkLabel(main_frame, text="База знаний для RP", font=T.FONT_SMALL, 
                     text_color=T.TEXT_MUTED).pack(pady=(0, 16))
        
        self.progress = ctk.CTkProgressBar(main_frame, width=300, height=6, 
                                           corner_radius=3, progress_color=T.DEFAULT_ACCENT)
        self.progress.pack(pady=(0, 12))
        self.progress.set(0)
        
        self.status_label = ctk.CTkLabel(main_frame, text="Инициализация…", 
                                          font=T.FONT_TINY, text_color=T.TEXT_MUTED)
        self.status_label.pack(pady=(0, 20))
        
        self._animate_progress()
        self.root.after(100, self._start_loading)
    
    def _animate_progress(self):
        if not hasattr(self, '_progress_val'):
            self._progress_val = 0
        self._progress_val = min(0.95, self._progress_val + 0.02)
        self.progress.set(self._progress_val)
        if self._progress_val < 0.95:
            self.root.after(80, self._animate_progress)
    
    def _start_loading(self):
        def worker():
            try:
                from core.bootstrap import run_bootstrap
                self._update_status("Проверка зависимостей…")
                run_bootstrap()
                
                self._update_status("Загрузка базы знаний…")
                time.sleep(0.1)
                
                self._update_status("Подготовка интерфейса…")
                time.sleep(0.1)
                
                self.root.after(0, self._on_done)
            except Exception as e:
                self.root.after(0, lambda: self._on_error(e))
        
        threading.Thread(target=worker, daemon=True).start()
    
    def _update_status(self, text):
        self.root.after(0, lambda: self.status_label.configure(text=text))
    
    def _on_done(self):
        self.progress.set(1.0)
        self.status_label.configure(text="Готово!")
        self.root.after(300, self._finish)
    
    def _finish(self):
        self.root.destroy()
        self.on_ready_callback()
    
    def _on_error(self, error):
        self.status_label.configure(text=f"Ошибка: {error}", text_color=T.WARNING)
        self.root.after(3000, self.root.destroy)
    
    def run(self):
        self.root.mainloop()


def show_splash(on_ready):
    splash = SplashScreen(on_ready)
    splash.run()