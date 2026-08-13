#!/usr/bin/env python3
"""
Генератор лицензионных ключей HelpeRP — ТОЛЬКО ДЛЯ ПРОДАВЦА.

  py tools/generate_license_key.py --init-keys   # создать пару ключей (один раз)
  py tools/generate_license_key.py               # 1 универсальный ключ
  py tools/generate_license_key.py 5               # 5 универсальных
  py tools/generate_license_key.py --bound         # ключ под текущий ПК
  py tools/generate_license_key.py --bound ABCD1234
"""

from __future__ import annotations

import argparse
import secrets
import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.licensing import get_machine_code, get_machine_code_display, validate_license_key  # noqa: E402
from tools.signing_private import ensure_keypair, sign_text  # noqa: E402


def generate_license_key(*, machine_bound: bool = False, machine_code: str | None = None) -> str:
    alphabet = string.ascii_uppercase + string.digits
    b = "".join(secrets.choice(alphabet) for _ in range(4))
    c = "".join(secrets.choice(alphabet) for _ in range(4))

    if machine_bound:
        mc = (machine_code or get_machine_code()).upper()[:8]
        payload = f"HELPE-{b}-{c}-{mc}"
    else:
        payload = f"HELPE-{b}-{c}"

    sig = sign_text(payload)
    return f"{payload}-{sig}"


def main():
    parser = argparse.ArgumentParser(description="Генератор ключей HelpeRP (Ed25519)")
    parser.add_argument("count", nargs="?", type=int, default=1, help="Количество ключей (1–100)")
    parser.add_argument("--bound", action="store_true", help="Ключ, привязанный к ПК")
    parser.add_argument("--init-keys", action="store_true", help="Создать пару Ed25519 ключей")
    parser.add_argument("machine_code", nargs="?", help="Код ПК покупателя (8 символов), с --bound")
    args = parser.parse_args()

    if args.init_keys:
        ensure_keypair()
        print("Пара ключей готова:")
        print("  Приватный: tools/.license_private.pem  (не включать в exe!)")
        print("  Публичный: core/license_public.bin")
        return

    ensure_keypair()
    count = max(1, min(100, args.count))
    mc = args.machine_code.upper()[:8] if args.machine_code else None

    print("HelpeRP — генератор лицензий (Ed25519 v2)\n")
    if args.bound:
        print(f"Тип: привязка к ПК · код машины: {mc or get_machine_code()}")
        print(f"Полный ID: {get_machine_code_display()}\n")
    else:
        print("Тип: универсальный\n")

    for _ in range(count):
        key = generate_license_key(machine_bound=args.bound, machine_code=mc)
        assert validate_license_key(key)
        print(key)

    print(f"\nСгенерировано: {count}.")


if __name__ == "__main__":
    main()
