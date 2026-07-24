# HelpeRP_Client/core/config.py
import os
import json

class Config:
    def __init__(self):
        # Имя файла, в котором намертво сохраняются все настройки пользователя
        self.config_filename = "settings.json"
        
        # Полные дефолтные настройки приложения при самом первом запуске
        self.default_settings = {
            "api_key": "YOUR_AI_API_KEY",
            "base_url": "https://openai.com",
            "model": "gpt-4o-mini",
            "current_faction": "Законодательство РФ",  # Название фракции по умолчанию
            "character": {
                "name": "Иван Иванов",
                "rank": "Рядовой",
                "badge": "№0000",
                "personality": "Вежливый, строго следует уставу, говорит уверенно"
            },
            "hotkeys": {
                "toggle_overlay": "shift+\\",  # Дефолтный настраиваемый хоткей
                "submit_request": "enter"
            }
        }
        
        self.settings = {}
        self.load_config()

    def load_config(self):
        """Загружает настройки с диска или создает новые, если файла нет"""
        if os.path.exists(self.config_filename):
            try:
                with open(self.config_filename, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
                
                # Глубокая проверка на случай, если в файле отсутствуют новые или важные ключи
                for key, value in self.default_settings.items():
                    if key not in self.settings:
                        self.settings[key] = value
                    # Проверяем вложенные словари (например, character и hotkeys)
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if sub_key not in self.settings[key]:
                                self.settings[key][sub_key] = sub_value
                                
            except Exception as e:
                print(f"[Config] Ошибка чтения {self.config_filename}: {e}. Сброс на настройки по умолчанию.")
                self.settings = self.default_settings.copy()
                self.save_config()
        else:
            # Если файла нет — создаем его с дефолтными настройками
            self.settings = self.default_settings.copy()
            self.save_config()

    def save_config(self):
        """Сохраняет текущее состояние настроек в файл settings.json"""
        try:
            with open(self.config_filename, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[Config] Не удалось сохранить настройки на диск: {e}")

    def get(self, key, default=None):
        """Безопасное получение любого верхнеуровневого параметра"""
        return self.settings.get(key, default)

    def set(self, key, value):
        """Установка параметра с автоматической мгновенной записью в JSON"""
        self.settings[key] = value
        self.save_config()

# Инициализируем глобальный объект конфигурации для импорта во все остальные модули софта
app_config = Config()
