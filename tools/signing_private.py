"""Подпись лицензий и manifest — ТОЛЬКО у продавца, не в exe."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIVATE_KEY_PATH = ROOT / "tools" / ".license_private.pem"
PUBLIC_BIN_PATH = ROOT / "core" / "license_public.bin"


def ensure_keypair() -> None:
    if PRIVATE_KEY_PATH.is_file() and PUBLIC_BIN_PATH.is_file():
        return

    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization

    private = Ed25519PrivateKey.generate()
    PRIVATE_KEY_PATH.write_bytes(
        private.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    PUBLIC_BIN_PATH.write_bytes(
        private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    )


def _load_private():
    from cryptography.hazmat.primitives import serialization

    ensure_keypair()
    return serialization.load_pem_private_key(PRIVATE_KEY_PATH.read_bytes(), password=None)


def sign_bytes(message: bytes) -> str:
    key = _load_private()
    return key.sign(message).hex().upper()


def sign_text(payload: str) -> str:
    return sign_bytes(payload.encode("utf-8"))


def sign_manifest(data: dict) -> str:
    from core.signing_public import canonical_json

    return sign_bytes(canonical_json(data))
