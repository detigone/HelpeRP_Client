"""Проверка лицензии HelpeRP — офлайн, привязка к ПК, без хранения ключа."""

from __future__ import annotations

import hashlib
import hmac
import os
import platform
import re
import uuid

from core.version import EULA_VERSION, PRODUCT_NAME, VERSION

# Смените перед релизом. Не включайте tools/ в buyer-сборку.
_LICENSE_SECRET = b"HelpeRP-2026-detigone-CHANGE-BEFORE-SALE"

# Универсальный: HELPE-BBBB-CCCC-SSSSSSSS
_KEY_UNIVERSAL = re.compile(r"^HELPE-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{8}$")
# Привязка к ПК: HELPE-BBBB-CCCC-MMMMMMMM-SSSSSSSS
_KEY_BOUND = re.compile(r"^HELPE-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{8}-[A-Z0-9]{8}$")


def _normalize_key(key: str) -> str:
    return key.strip().upper().replace(" ", "")


def get_machine_id() -> str:
    """Стабильный ID машины для привязки лицензии."""
    node = uuid.getnode()
    raw = f"{platform.system()}|{platform.node()}|{node}|{PRODUCT_NAME}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_machine_code() -> str:
    """Короткий код ПК для ключей и поддержки."""
    return get_machine_id()[:8].upper()


def get_machine_code_display() -> str:
    mid = get_machine_id()
    return f"{mid[:8]}-{mid[8:16]}-{mid[16:24]}".upper()


def _sign(payload: str) -> str:
    digest = hmac.new(_LICENSE_SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest[:8].upper()


def activation_token(fingerprint: str, machine_id: str | None = None) -> str:
    machine_id = machine_id or get_machine_id()
    return hmac.new(
        _LICENSE_SECRET,
        f"activate:{fingerprint}:{machine_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def license_key_fingerprint(key: str) -> str:
    return hashlib.sha256(_normalize_key(key).encode("utf-8")).hexdigest()


def generate_license_key(*, machine_bound: bool = False, machine_code: str | None = None) -> str:
    """Генерация ключа (только продавец, tools/generate_license_key.py)."""
    import secrets
    import string

    alphabet = string.ascii_uppercase + string.digits
    b = "".join(secrets.choice(alphabet) for _ in range(4))
    c = "".join(secrets.choice(alphabet) for _ in range(4))

    if machine_bound:
        mc = (machine_code or get_machine_code()).upper()[:8]
        payload = f"HELPE-{b}-{c}-{mc}"
    else:
        payload = f"HELPE-{b}-{c}"

    sig = _sign(payload)
    return f"{payload}-{sig}"


def _parse_key(key: str) -> tuple[str, str, bool] | None:
    """Возвращает (payload, signature, is_bound) или None."""
    key = _normalize_key(key)
    if _KEY_BOUND.match(key):
        payload, sig = key.rsplit("-", 1)
        return payload, sig, True
    if _KEY_UNIVERSAL.match(key):
        payload, sig = key.rsplit("-", 1)
        return payload, sig, False
    return None


def license_key_error_hint(key: str) -> str | None:
    """Подсказка при типичных ошибках ввода ключа."""
    norm = _normalize_key(key)
    if validate_license_key(norm):
        return None
    if norm.startswith("HEPLE-") and validate_license_key(norm.replace("HEPLE-", "HELPE-", 1)):
        return "Опечатка: ключ начинается с HELPE, а не HEPLE."
    if norm.startswith("HELPER-"):
        return "Ключ начинается с HELPE-, не HELPER-."
    return None


def validate_license_key(key: str) -> bool:
    parsed = _parse_key(key)
    if not parsed:
        return False
    payload, sig, is_bound = parsed
    if not hmac.compare_digest(_sign(payload), sig):
        return False
    if is_bound:
        parts = payload.split("-")
        if len(parts) != 4:
            return False
        key_machine = parts[3]
        if key_machine != get_machine_code():
            return False
    return True


def license_key_type(key: str) -> str:
    parsed = _parse_key(key)
    if not parsed:
        return "invalid"
    return "bound" if parsed[2] else "universal"


def is_dev_mode() -> bool:
    if os.environ.get("HELPERP_DEV", "").strip().lower() in ("1", "true", "yes"):
        return True
    from core.paths import app_dir
    return os.path.isfile(os.path.join(app_dir(), ".helperp_dev"))


def activate_license(key: str, *, eula_version: str = EULA_VERSION) -> dict:
    """Проверяет ключ и возвращает блок license для settings (без plaintext key)."""
    from datetime import datetime, timezone

    if is_dev_mode() and not key:
        return {
            "eula_accepted": True,
            "eula_version": eula_version,
            "dev_mode": True,
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "product_version": VERSION,
        }

    norm = _normalize_key(key)
    if not validate_license_key(norm):
        raise ValueError("invalid_key")

    fp = license_key_fingerprint(norm)
    machine_id = get_machine_id()
    token = activation_token(fp, machine_id)
    ltype = license_key_type(norm)

    return {
        "eula_accepted": True,
        "eula_version": eula_version,
        "key_fingerprint": fp,
        "activation_token": token,
        "key_last4": norm[-4:],
        "license_type": ltype,
        "machine_id": machine_id,
        "machine_code": get_machine_code(),
        "activated_at": datetime.now(timezone.utc).isoformat(),
        "product_version": VERSION,
    }


def migrate_license_cfg(license_cfg: dict | None) -> dict:
    """Убирает plaintext key из конфига, создаёт token если есть ключ."""
    if not license_cfg:
        return {}
    cfg = dict(license_cfg)
    key = cfg.pop("key", "")
    if key and validate_license_key(key):
        try:
            fresh = activate_license(key, eula_version=cfg.get("eula_version", EULA_VERSION))
            cfg.update(fresh)
        except ValueError:
            pass
    return cfg


def is_licensed(license_cfg: dict | None) -> bool:
    if is_dev_mode():
        return True
    if not license_cfg or not license_cfg.get("eula_accepted"):
        return False
    if license_cfg.get("dev_mode") and is_dev_mode():
        return True

    fp = license_cfg.get("key_fingerprint", "")
    token = license_cfg.get("activation_token", "")
    if fp and token:
        if license_cfg.get("machine_id") and license_cfg["machine_id"] != get_machine_id():
            return False
        expected = activation_token(fp, get_machine_id())
        if hmac.compare_digest(token, expected):
            return True

    # Legacy: plaintext key (мигрируется при save)
    key = license_cfg.get("key", "")
    return bool(key) and validate_license_key(key)


def license_status_text(license_cfg: dict | None) -> str:
    if is_dev_mode():
        return "Режим разработки"
    if not license_cfg or not license_cfg.get("eula_accepted"):
        return "Не активирована"
    if not is_licensed(license_cfg):
        if license_cfg.get("machine_id") and license_cfg.get("machine_id") != get_machine_id():
            return "Лицензия привязана к другому ПК"
        return "Не активирована"
    last4 = license_cfg.get("key_last4", "????")
    ltype = license_cfg.get("license_type", "universal")
    kind = "ПК" if ltype == "bound" else "универсальная"
    return f"Активна ({kind}) · ···{last4}"


def product_banner_line() -> str:
    return f"{PRODUCT_NAME} v{VERSION}"
