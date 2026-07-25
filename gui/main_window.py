# HelpeRP_Client/gui/main_window.py
import customtkinter as ctk
import json
import os
import threading
from core.config import app_config

class HelpeRPMainWindow:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        self.root = ctk.CTk()
        self.root.title("HelpeRP — База Знаний")
        self.root.attributes("-topmost", True)
        
        self.width = 950
        self.height = 620
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw // 2) - (self.width // 2)
        y = (sh // 2) - (self.height // 2)
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

        self.is_visible = True
        self.all_laws = []
        self.load_laws_database()
        self.create_ui()

    def load_laws_database(self):
        """Загрузка выбранной базы данных фракции"""
        fac = app_config.get("current_faction", "Законодательство РФ")
        
        if fac == "Законодательство РФ":
            path = "data/legislation_rf.json"
        elif fac == "МЧС":
            path = "data/mchs.json"
        else:
            path = "data/smp.json"

        if not os.path.exists(path):
            self.load_fallback_data()
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if isinstance(data, dict) and "codes" in data:
                flat = []
                for c_name, arts in data["codes"].items():
                    for a in arts:
                        a["title"] = f"[{c_name[:5]}] {a['title']}"
                        flat.append(a)
                self.all_laws = flat
            elif isinstance(data, dict) and "emergency_protocols" in data:
                self.all_laws = data["emergency_protocols"]
            elif isinstance(data, dict) and "medical_protocols" in data:
                self.all_laws = data["medical_protocols"]
            else:
                self.all_laws = data if isinstance(data, list) else []
        except Exception as e:
            print(f"[Ошибка JSON]: {e}")
            self.load_fallback_data()

    def load_fallback_data(self):
        """Резервные данные если файлов нет на диске"""
        self.all_laws = [
            {"article": "105", "title": "Статья 105 УК РФ", 
             "description": "Убийство.", "is_frequent": True},
            {"article": "228", "title": "Статья 228 УК РФ", 
             "description": "Наркотики.", "is_frequent": True}
        ]
    def create_ui(self):
        """Создание сетки и элементов управления"""
        self.root.grid_columnconfigure(0, weight=0, minsize=340)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Левая колонка
        self.left_frame = ctk.CTkFrame(
            self.root, fg_color="#1e1f22", corner_radius=0
        )
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        
        self.faction_selector = ctk.CTkComboBox(
            self.left_frame,
            values=["Законодательство РФ", "МЧС", "СМП"],
            height=32, command=self.change_faction
        )
        self.faction_selector.pack(fill="x", padx=15, pady=(15, 5))
        self.faction_selector.set(
            app_config.get("current_faction", "Законодательство РФ")
        )
        
        self.search_entry = ctk.CTkEntry(
            self.left_frame, placeholder_text="🔍 Поиск...", height=35
        )
        self.search_entry.pack(fill="x", padx=15, pady=10)
        self.search_entry.bind("<KeyRelease>", self.filter_laws)

        self.scroll_list = ctk.CTkScrollableFrame(
            self.left_frame, fg_color="transparent"
        )
        self.scroll_list.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        # Правая колонка
        self.right_frame = ctk.CTkFrame(
            self.root, fg_color="#111214", corner_radius=0
        )
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)

        self.law_title_label = ctk.CTkLabel(
            self.right_frame, text="Выберите элемент", 
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#00f0ff"
        )
        self.law_title_label.pack(anchor="w", padx=25, pady=15)

        self.textbox = ctk.CTkTextbox(
            self.right_frame, font=ctk.CTkFont(size=13), 
            fg_color="#1e1f22", border_width=1, border_color="#2b2d31"
        )
        self.textbox.pack(fill="both", expand=True, padx=25, pady=5)
        self.textbox.configure(state="disabled")

        self.action_frame = ctk.CTkFrame(
            self.right_frame, fg_color="transparent"
        )
        self.action_frame.pack(fill="x", padx=25, pady=15)

        self.btn_copy = ctk.CTkButton(
            self.action_frame, text="📋 Скопировать", 
            fg_color="#2b2d31", hover_color="#00f0ff", 
            command=self.copy_law_text
        )
        self.btn_copy.pack(side="left", padx=5)

        self.btn_ai = ctk.CTkButton(
            self.action_frame, text="✨ Отыграть ИИ", 
            fg_color="#1f538d", hover_color="#2ecc71", 
            command=self.trigger_ai_action
        )
        self.btn_ai.pack(side="right", padx=5)

        self.populate_list(self.all_laws)
    def populate_list(self, laws_list):
        """Обновление левого списка кнопок"""
        for widget in self.scroll_list.winfo_children():
            widget.destroy()

        for law in laws_list:
            prefix = "⭐ " if law.get("is_frequent") else ""
            btn = ctk.CTkButton(
                self.scroll_list, text=f"{prefix}{law['title']}",
                anchor="w", fg_color="transparent", text_color="#ffffff",
                hover_color="#2b2d31", height=32,
                command=lambda item=law: self.display_law(item)
            )
            btn.pack(fill="x", pady=2, padx=5)

    def display_law(self, law):
        """Отображение текста элемента на экране"""
        self.current_selected_law = law
        self.law_title_label.configure(
            text=law['title'], text_color="#00f0ff"
        )
        
        self.textbox.configure(state="normal")
        self.textbox.delete("0.0", "end")
        
        desc = law.get('description', law.get('protocol', law.get('text', '')))
        self.textbox.insert("0.0", desc)
        self.textbox.configure(state="disabled")

    def change_faction(self, selected_faction):
        app_config.set("current_faction", selected_faction)
        self.load_laws_database()
        self.populate_list(self.all_laws)

    def filter_laws(self, event=None):
        """Фильтр локальной базы + живой интернет-поиск"""
        query = self.search_entry.get().lower().strip()
        if not query:
            self.populate_list(self.all_laws)
            return

        filtered = [
            l for l in self.all_laws 
            if query in str(l.get('article', '')).lower() 
            or query in l['title'].lower() 
            or any(query in kw for kw in l.get('keywords', []))
        ]
        self.populate_list(filtered)

        if len(filtered) == 0 and len(query) > 3:
            self.law_title_label.configure(
                text="🌐 Ищу в интернете...", text_color="#ff9900"
            )
            
            def bg_search():
                try:
                    from core.online_search import search_law_online
                    fac = self.faction_selector.get()
                    txt = search_law_online(query, faction_context=fac)
                    if txt:
                        self.root.after(
                            0, lambda: self.update_ui_with_online_data(query, txt)
                        )
                    else:
                        self.root.after(
                            0, lambda: self.law_title_label.configure(
                                text="❌ Не найдено", text_color="red"
                            )
                        )
                except Exception as e:
                    print(f"Ошибка поиска: {e}")
            
            threading.Thread(target=bg_search, daemon=True).start()

    def update_ui_with_online_data(self, query, text):
        self.law_title_label.configure(
            text=f"🌐 Из сети: {query}", text_color="#00f0ff"
        )
        self.textbox.configure(state="normal")
        self.textbox.delete("0.0", "end")
        self.textbox.insert("0.0", text)
        self.textbox.configure(state="disabled")
        self.current_selected_law = {"title": query, "description": text}

    def copy_law_text(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.textbox.get("0.0", "end").strip())

    def trigger_ai_action(self):
        """Генерация RP-строк на основе текста на экране"""
        current_text = self.textbox.get("0.0", "end").strip()
        self.law_title_label.configure(
            text="⏳ ИИ формирует отыгровку...", text_color="#ff9900"
        )
        self.root.update()
        
        def bg_ai():
            try:
                from core.ai_client import rp_ai
                from core.hotkeys import send_rp_sequence
                lines = rp_ai.generate_rp_commands(
                    f"Сделай отыгровку по тексту:\n{current_text}"
                )
                self.root.after(
                    0, lambda: self.law_title_label.configure(
                        text="✅ Готово!", text_color="#2ecc71"
                    )
                )
                send_rp_sequence(lines)
            except Exception as e:
                print(f"Ошибка ИИ: {e}")
                
        threading.Thread(target=bg_ai, daemon=True).start()

    def toggle_visibility(self):
        if self.is_visible:
            self.root.withdraw()
            self.is_visible = False
        else:
            self.root.deiconify()
            self.is_visible = True

    def start(self):
        self.root.mainloop()
