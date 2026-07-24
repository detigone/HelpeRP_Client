# HelpeRP_Client/gui/main_window.py
import customtkinter as ctk
import json
import os
from core.config import app_config
from core.ai_client import rp_ai
from core.hotkeys import send_rp_sequence

class HelpeRPMainWindow:
    def __init__(self):
        # Настраиваем глубокую темную тему
        ctk.set_appearance_mode("dark")
        
        self.root = ctk.CTk()
        self.root.title("HelpeRP Overlay")
        
        # Полный оверлей: убираем рамки Windows, окно всегда на переднем плане
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        
        # Чуть увеличим размеры для красивых отступов
        self.width = 580
        self.height = 190
        
        # Идеальное центрирование на экране (чуть выше центра)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (self.width // 2)
        y = (screen_height // 4)
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        # Делаем окно стильно-полупрозрачным
        self.root.attributes("-alpha", 0.96)

        # Цветовая палитра софта
        self.color_idle = "#00f0ff"       # Неоновый голубой (ожидание)
        self.color_processing = "#ff9900" # Оранжевый (ИИ думает)
        self.color_success = "#2ecc71"    # Зеленый (успех)
        self.bg_dark = "#111214"          # Ультра-темный фон

        self.is_visible = True
        self.create_ui()

    def create_ui(self):
        """Создание премиального киберспортивного интерфейса"""
        # Главный фрейм приложения со светящейся неоновой рамкой
        self.main_frame = ctk.CTkFrame(
            self.root, 
            corner_radius=16, 
            border_width=2, 
            border_color=self.color_idle,
            fg_color=self.bg_dark
        )
        self.main_frame.pack(fill="both", expand=True, padx=3, pady=3)

        # 1. ШАПКА ИНТЕРФЕЙСА
        self.top_bar = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=20, pady=(15, 5))

        # Текст логотипа с красивым шрифтом
        self.logo_label = ctk.CTkLabel(
            self.top_bar, 
            text="🤖 Helpe", 
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#ffffff"
        )
        self.logo_label.pack(side="left")
        
        # Выделяем буквы RP неоновым цветом
        self.logo_rp = ctk.CTkLabel(
            self.top_bar, 
            text="RP", 
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.color_idle
        )
        self.logo_rp.pack(side="left")

        # Текст текущего статуса
        self.title_label = ctk.CTkLabel(
            self.top_bar, 
            text="  |  Система готова", 
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#a0a0a0"
        )
        self.title_label.pack(side="left")

        # Дизайнерский выпадающий список выбора фракций
        self.faction_selector = ctk.CTkComboBox(
            self.top_bar,
            values=["Законодательство РФ", "МЧС", "СМП"],
            width=190,
            height=28,
            corner_radius=8,
            fg_color="#1e1f22",
            border_color="#2b2d31",
            button_color="#2b2d31",
            button_hover_color=self.color_idle,
            dropdown_fg_color="#1e1f22",
            dropdown_hover_color="#2b2d31",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.change_faction
        )
        self.faction_selector.pack(side="right")
        current_fac = app_config.get("current_faction", "Законодательство РФ")
        self.faction_selector.set(current_fac)

        # 2. ЗОНА ВВОДА С КОНТРАСТНЫМ ФОНОМ
        self.input_container = ctk.CTkFrame(self.main_frame, fg_color="#1e1f22", corner_radius=10)
        self.input_container.pack(fill="x", padx=20, pady=10)

        self.input_entry = ctk.CTkEntry(
            self.input_container, 
            placeholder_text=" Наговорите или введите ситуацию (например: ножевое ранение в живот)...",
            width=520,
            height=42,
            corner_radius=8,
            fg_color="transparent",
            border_width=0, # Убираем стандартную рамку ввода для бесшовного стиля
            text_color="#ffffff",
            placeholder_text_color="#606060",
            font=ctk.CTkFont(family="Segoe UI", size=13)
        )
        self.input_entry.pack(fill="x", padx=5, pady=2)
        self.input_entry.bind("<Return>", self.handle_submit)

        # 3. ПОДВАЛ (ХОТКЕИ)
        self.footer_label = ctk.CTkLabel(
            self.main_frame, 
            text="⚡ [Alt + Space] — Скрыть оверлей    •    [Enter] — Запустить ИИ-суфлер", 
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#505050"
        )
        self.footer_label.pack(pady=(0, 10))

    def change_faction(self, selected_faction):
        app_config.set("current_faction", selected_faction)
        print(f"[HelpeRP UI] Контекст переключен: {selected_faction}")

    def toggle_visibility(self):
        if self.is_visible:
            self.root.withdraw()
            self.is_visible = False
        else:
            self.root.deiconify()
            self.root.attributes("-topmost", True)
            self.input_entry.focus()
            self.is_visible = True

    def handle_submit(self, event=None):
        user_query = self.input_entry.get().strip()
        if not user_query:
            return

        # Меняем тему на «Процессинг» (Оранжевое свечение рамки)
        self.main_frame.configure(border_color=self.color_processing)
        self.title_label.configure(text="  |  ИИ генерирует отыгровки...", text_color=self.color_processing)
        self.logo_rp.configure(text_color=self.color_processing)
        self.root.update()

        # Запрос к ИИ
        generated_lines = rp_ai.generate_rp_commands(user_query)

        # Очищаем ввод и меняем тему на «Успех» (Зеленое свечение)
        self.input_entry.delete(0, 'end')
        self.main_frame.configure(border_color=self.color_success)
        self.title_label.configure(text="  |  Текст отправлен в игру!", text_color=self.color_success)
        self.logo_rp.configure(text_color=self.color_success)
        self.root.update()

        # Отправка в игровой чат
        send_rp_sequence(generated_lines)

        # Авто-скрытие оверлея через 1.5 секунды
        self.root.after(1500, self.reset_ui_status)

    def reset_ui_status(self):
        # Возвращаем красивый неоновый стиль оглавления
        self.main_frame.configure(border_color=self.color_idle)
        self.title_label.configure(text="  |  Система готова", text_color="#a0a0a0")
        self.logo_rp.configure(text_color=self.color_idle)
        if self.is_visible:
            self.toggle_visibility()

    def start(self):
        self.input_entry.focus()
        self.root.mainloop()
