"""Публичный ключ Ed25519 для проверки лицензий и manifest (без секрета)."""

from __future__ import annotations

import json
from pathlib import Path

_PUBLIC_BIN = Path(__file__).with_name("license_public.bin")

_TRUSTED_MANIFEST_HOSTS = (
    "yeolka-lm.github.io",
    "github.com",
    "raw.githubusercontent.com",
)


def _public_key():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    if not _PUBLIC_BIN.is_file():
        raise FileNotFoundError("license_public.bin не найден — запустите tools/generate_license_key.py --init-keys")
    raw = _PUBLIC_BIN.read_bytes()
    return Ed25519PublicKey.from_public_bytes(raw)


def verify_signature(message: bytes, signature_hex: str) -> bool:
    try:
        sig = bytes.fromhex(signature_hex.strip())
        _public_key().verify(sig, message)
        return True
    except Exception:
        return False


def canonical_json(data: dict) -> bytes:
    clean = {k: v for k, v in data.items() if k != "signature"}
    return json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def verify_manifest(data: dict) -> bool:
    sig = str(data.get("signature") or "").strip()
    if not sig:
        return False
    return verify_signature(canonical_json(data), sig)


def is_trusted_update_url(url: str) -> bool:
    u = (url or "").strip().lower()
    if not u.startswith("https://"):
        return False
    from core.build_config import RELEASE_BUILD

    if not RELEASE_BUILD:
        return True
    host = u.split("/")[2].split(":")[0]
    return any(host == h or host.endswith("." + h) for h in _TRUSTED_MANIFEST_HOSTS)
