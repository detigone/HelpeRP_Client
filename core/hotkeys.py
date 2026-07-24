# HelpeRP_Client/core/hotkeys.py
import pydirectinput
import pyautogui
import pyperclip
import time
import random
import threading
import keyboard

# Configure pydirectinput for safe DirectX level key injection
pydirectinput.PAUSE = 0.01

def send_to_chat(text: str):
    """
    Opens the game chat, pastes the text using clipboard to prevent bugs, 
    and hits Enter with randomized human-like delays.
    """
    if not text.strip():
        return
        
    try:
        # 1. Open game chat. Usually 't' or 'f6' in SAMP/CRMP/GTA 5 RP
        pydirectinput.press('t')
        time.sleep(random.uniform(0.1, 0.18))

        # 2. Safely push text into Windows clipboard and paste it
        pyperclip.copy(text)
        pydirectinput.keyDown('ctrl')
        pydirectinput.press('v')
        pydirectinput.keyUp('ctrl')
        time.sleep(random.uniform(0.05, 0.12))

        # 3. Submit message
        pydirectinput.press('enter')
        print(f"[HelpeRP Chat] Sent: {text}")
        
    except Exception as e:
        print(f"[HelpeRP Chat] Input error: {e}")

def send_rp_sequence(lines: list):
    """
    Sends multiple lines of /me, /do, /todo or speech one by one 
    with dynamic time gaps to avoid server flood kicks or bans.
    """
    def worker():
        for line in lines:
            cleaned_line = line.strip()
            if cleaned_line:
                send_to_chat(cleaned_line)
                # Human typing break (0.7 to 1.3 seconds per line)
                time.sleep(random.uniform(0.7, 1.3))
                
    # Run in a background thread so it doesn't freeze the app overlay
    threading.Thread(target=worker, daemon=True).start()

def register_global_hotkey(hotkey_str: str, callback_func):
    """
    Registers a background listener for hotkeys (e.g. alt+space) 
    to summon or dismiss the UI over any fullscreen game.
    """
    try:
        keyboard.add_hotkey(hotkey_str, callback_func)
    except Exception as e:
        print(f"[HelpeRP Hotkeys] Failed to bind {hotkey_str}: {e}")
