# HelpeRP_Client/run.py
import sys
import os
import threading
import keyboard
from core.config import app_config
from gui.main_window import HelpeRPMainWindow

def main():
    print("====================================================")
    print("🤖 HelpeRP — Программа оцифрованного законодательства")
    print("====================================================")
    
    # Инициализируем окно. Оно автоматически откроется на экране!
    overlay = HelpeRPMainWindow()
    
    toggle_key = app_config.get("hotkeys", {}).get("toggle_overlay", "shift+\\")
    print(f"[Система] Хоткей сворачивания/закрытия окна: [{toggle_key.upper()}]")

    def on_hotkey_pressed():
        overlay.toggle_visibility()

    try:
        # Регистрируем Shift + \ для мгновенного скрытия/показа окна прямо во время игры
        keyboard.add_hotkey(toggle_key, on_hotkey_pressed)
    except Exception as e:
        print(f"[Ошибка хоткея]: {e}")

    # Запускаем бесконечный рабочий цикл отображения интерфейса
    overlay.start()

if __name__ == "__main__":
    main()
