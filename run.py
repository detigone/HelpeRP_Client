# HelpeRP_Client/run.py
import sys
import os
import threading
import keyboard
from core.config import app_config
from gui.main_window import HelpeRPMainWindow

def main():
    print("====================================================")
    print("🤖 HelpeRP — ИИ-Ассистент гос. структур успешно запущен!")
    print("====================================================")
    
    # 1. Инициализируем главное графическое окно оверлея
    overlay = HelpeRPMainWindow()
    
    # Получаем настроенный хоткей из конфигурации (дефолт: shift+\)
    toggle_key = app_config.get("hotkeys", {}).get("toggle_overlay", "shift+\\")
    
    print(f"[Ядро] Хоткей активации оверлея: [{toggle_key.upper()}]")
    print("[Ядро] Приложение работает в фоне. Сверните консоль и войдите в игру.")

    # 2. Функция-обработчик нажатия клавиши
    def on_hotkey_pressed():
        # Вызываем метод переключения видимости окна из gui/main_window.py
        overlay.toggle_visibility()

    # 3. Запускаем глобальный перехват клавиш в отдельном фоновом потоке.
    # Это нужно, чтобы клавиатура слушалась даже тогда, когда игра развернута на весь экран.
    try:
        keyboard.add_hotkey(toggle_key, on_hotkey_pressed)
    except Exception as e:
        print(f"[Критическая ошибка] Не удалось зарегистрировать хоткей {toggle_key}: {e}")
        print("Попробуйте запустить приложение от имени Администратора.")
        sys.exit(1)

    # Принудительно прячем окно при самом первом запуске, чтобы оно не мешало рабочему столу
    overlay.toggle_visibility()

    # 4. Запускаем бесконечный цикл обработки графического интерфейса Tkinter
    overlay.start()

if __name__ == "__main__":
    # Проверяем наличие папки с базами данных перед запуском для стабильности софта
    if not os.path.exists("data"):
        print("[Внимание] Папка 'data' не найдена. Создайте её и загрузите JSON-базы фракций!")
    
    main()
