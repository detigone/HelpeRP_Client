# HelpeRP_Client/run.py

import threading
from core.bootstrap import run_bootstrap
from core.config import app_config

from core.discord_presence import start_discord_presence, stop_discord_presence
from core.hotkey_manager import rebind_all_from_config

from core.licensing import is_licensed, product_banner_line

from gui.main_window import HelpeRPMainWindow


def _init_discord_presence_safe():
    """Инициализация Discord RPC в отдельном потоке."""
    try:
        start_discord_presence()
    except Exception as exc:
        print(f"[Discord] Ошибка инициализации: {exc}")





def _launch_app():

    overlay = HelpeRPMainWindow()

    rebind_all_from_config(overlay)



    toggle = app_config.get("hotkeys", {}).get("toggle_overlay", "shift+\\")

    hide = app_config.get("hotkeys", {}).get("hide_window", "ctrl+shift+h")

    print(f"[Система] {toggle.upper()} — компакт/развёрнутый")

    print(f"[Система] {hide.upper()} — скрыть/показать окно")



    def on_settings_saved():

        rebind_all_from_config(overlay)

        overlay._on_settings_saved()

        from core.discord_presence import refresh_discord_presence
        try:
            refresh_discord_presence()
        except Exception as exc:
            print(f"[Discord] Ошибка обновления при сохранении: {exc}")



    overlay._settings_saved_callback = on_settings_saved

    overlay.start()





def _run_license_gate():

    import customtkinter as ctk

    from gui.license_dialog import LicenseDialog



    ctk.set_appearance_mode("dark")

    root = ctk.CTk()

    root.withdraw()

    activated = {"ok": False}



    def on_activated():

        activated["ok"] = True

        root.quit()



    LicenseDialog(root, on_activated=on_activated)

    root.mainloop()

    root.destroy()

    return activated["ok"] and is_licensed(app_config.get("license"))





def main():
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    print("====================================================")

    print(product_banner_line())

    print("  База · меры · ИИ · лицензия Professional")

    print("====================================================")
    
    # Инициализация и проверка всех зависимостей
    print()
    if not run_bootstrap():
        print("[Система] ⚠ Bootstrap завершён с ошибками, но приложение продолжит работу")
        print()

    try:
        if not is_licensed(app_config.get("license")):

            print("[Лицензия] Требуется активация…")

            if not _run_license_gate():

                print("[Лицензия] Выход без активации.")

                return

        # Инициализация Discord RPC в фоновом потоке (не блокирует запуск)
        discord_thread = threading.Thread(target=_init_discord_presence_safe, daemon=True, name="discord-init")
        discord_thread.start()
        
        _launch_app()
    except Exception as exc:
        print(f"[Ошибка] Критическая ошибка приложения: {exc}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            stop_discord_presence()
        except Exception:
            pass





if __name__ == "__main__":

    main()

