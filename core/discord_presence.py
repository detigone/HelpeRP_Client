import logging
import threading
from typing import Optional

try:
    import pypresence
except Exception:  # pragma: no cover
    pypresence = None

from core.config import app_config

logger = logging.getLogger(__name__)

_LOCK = threading.RLock()
_RPC: Optional["pypresence.Presence"] = None
_WATCHER_THREAD: Optional[threading.Thread] = None
_STOP_EVENT = threading.Event()
_LAST_ACTIVITY = {"details": None, "state": None}
_RECONNECT_INTERVAL = 15  # сек между попытками переподключения


def _discord_cfg() -> dict:
    return app_config.get("discord", {}) or {}


def _button_payload(cfg: dict) -> list[dict]:
    return [{
        "label": cfg.get("button_label", "Открыть HelpeRP"),
        "url": cfg.get("button_url", "https://yeolka-lm.github.io/HelpeRP_Client/"),
    }]


def _connect_locked(cfg: dict) -> bool:
    """Вызывать только под _LOCK."""
    global _RPC

    client_id = str(cfg.get("client_id", "")).strip()
    if not client_id or pypresence is None:
        return False

    if _RPC is not None:
        try:
            _RPC.close()
        except Exception:
            pass
        _RPC = None

    try:
        rpc = pypresence.Presence(client_id)
        rpc.connect()
        _RPC = rpc
        _apply_activity_locked(cfg)
        logger.info("Discord RPC подключен")
        return True
    except Exception as exc:
        logger.warning("Discord RPC: не удалось подключиться: %s", exc)
        _RPC = None
        return False


def _apply_activity_locked(cfg: dict, details: str | None = None, state: str | None = None):
    """Вызывать только под _LOCK."""
    global _RPC
    if _RPC is None:
        return

    details = details or _LAST_ACTIVITY["details"] or cfg.get("details", "HelpeRP — база знаний")
    state = state or _LAST_ACTIVITY["state"] or cfg.get("state", "Режим поиска и подготовки RP")

    try:
        _RPC.update(
            details=details,
            state=state,
            large_image=cfg.get("large_image", "logo"),
            large_text=cfg.get("large_text", "HelpeRP"),
            buttons=_button_payload(cfg),
        )
        _LAST_ACTIVITY["details"] = details
        _LAST_ACTIVITY["state"] = state
    except Exception as exc:
        logger.debug("Discord RPC: update не удался, сбрасываю соединение: %s", exc)
        try:
            _RPC.close()
        except Exception:
            pass
        _RPC = None


def _watcher_loop():
    """Фоновый поток: пока фича включена, пытается держать соединение живым."""
    while not _STOP_EVENT.is_set():
        cfg = _discord_cfg()
        if cfg.get("enabled", False):
            with _LOCK:
                if _RPC is None:
                    _connect_locked(cfg)
        _STOP_EVENT.wait(_RECONNECT_INTERVAL)


def start_discord_presence():
    global _WATCHER_THREAD

    _STOP_EVENT.clear()
    cfg = _discord_cfg()
    if cfg.get("enabled", False):
        with _LOCK:
            _connect_locked(cfg)

    if _WATCHER_THREAD is None or not _WATCHER_THREAD.is_alive():
        _WATCHER_THREAD = threading.Thread(
            target=_watcher_loop, name="discord-rpc-watcher", daemon=True
        )
        _WATCHER_THREAD.start()


def refresh_discord_presence():
    """Перечитать конфиг и включить/выключить presence соответственно."""
    cfg = _discord_cfg()
    if not cfg.get("enabled", False):
        stop_discord_presence()
        return
    start_discord_presence()


def stop_discord_presence():
    global _RPC

    _STOP_EVENT.set()
    with _LOCK:
        if _RPC is not None:
            try:
                _RPC.clear()
            except Exception:
                pass
            try:
                _RPC.close()
            except Exception:
                pass
            _RPC = None


def update_discord_presence_from_state(details: str | None = None, state: str | None = None):
    cfg = _discord_cfg()
    if not cfg.get("enabled", False):
        return

    with _LOCK:
        if _RPC is None:
            if not _connect_locked(cfg):
                return
        _apply_activity_locked(cfg, details=details, state=state)