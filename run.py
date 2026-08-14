# HelpeRP_Client/run.py

from core.config import app_config

from core.discord_presence import start_discord_presence, stop_discord_presence
from core.hotkey_manager import rebind_all_from_config

from core.licensing import is_licensed, product_banner_line

from gui.main_window import HelpeRPMainWindow





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
        refresh_discord_presence()



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

    print("====================================================")

    print(product_banner_line())

    print("  База · меры · ИИ · лицензия Professional")

    print("====================================================")

    try:
        if not is_licensed(app_config.get("license")):

            print("[Лицензия] Требуется активация…")

            if not _run_license_gate():

                print("[Лицензия] Выход без активации.")

                return

        start_discord_presence()
        _launch_app()
    finally:
        stop_discord_presence()





if __name__ == "__main__":

    main()

