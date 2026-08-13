#!/usr/bin/env python3
"""
Генератор лицензионных ключей HelpeRP — ТОЛЬКО ДЛЯ ПРОДАВЦА.

  py tools/generate_license_key.py           # 1 универсальный ключ
  py tools/generate_license_key.py 5         # 5 универсальных
  py tools/generate_license_key.py --bound   # ключ под текущий ПК
  py tools/generate_license_key.py --bound ABCD1234  # под код ПК покупателя
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.licensing import generate_license_key, get_machine_code, get_machine_code_display  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Генератор ключей HelpeRP")
    parser.add_argument("count", nargs="?", type=int, default=1, help="Количество ключей (1–100)")
    parser.add_argument("--bound", action="store_true", help="Ключ, привязанный к ПК")
    parser.add_argument("machine_code", nargs="?", help="Код ПК покупателя (8 символов), с --bound")
    args = parser.parse_args()

    count = max(1, min(100, args.count))
    mc = args.machine_code.upper()[:8] if args.machine_code else None

    print("HelpeRP — генератор лицензий\n")
    if args.bound:
        print(f"Тип: привязка к ПК · код машины: {mc or get_machine_code()}")
        print(f"Полный ID (для поддержки): {get_machine_code_display()}\n")
    else:
        print("Тип: универсальный (1 ключ = 1 покупка, без привязки к железу)\n")

    for _ in range(count):
        print(generate_license_key(machine_bound=args.bound, machine_code=mc))

    print(f"\nСгенерировано: {count}. Один ключ — одна лицензия.")


if __name__ == "__main__":
    main()
