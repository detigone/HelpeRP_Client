# HelpeRP_Client/core/hotkeys.py
import time
import random
import threading

import keyboard
import pydirectinput
import pyperclip

from core.config import app_config

pydirectinput.PAUSE = 0.01


def _chat_key() -> str:
    return app_config.get("game", {}).get("chat_key", "t") or "t"


def send_to_chat(text: str):
    if not text.strip():
        return
    try:
        pydirectinput.press(_chat_key())
        time.sleep(random.uniform(0.1, 0.18))
        pyperclip.copy(text)
        pydirectinput.keyDown("ctrl")
        pydirectinput.press("v")
        pydirectinput.keyUp("ctrl")
        time.sleep(random.uniform(0.05, 0.12))
        pydirectinput.press("enter")
        print(f"[HelpeRP Chat] Sent: {text[:80]}")
    except Exception as e:
        print(f"[HelpeRP Chat] Input error: {e}")


def send_rp_sequence(lines: list):
    def worker():
        for line in lines:
            cleaned = line.strip()
            if cleaned:
                send_to_chat(cleaned)
                time.sleep(random.uniform(0.7, 1.3))

    threading.Thread(target=worker, daemon=True).start()

