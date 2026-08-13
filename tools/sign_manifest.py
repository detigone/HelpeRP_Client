#!/usr/bin/env python3
"""Подписать updates/manifest.json Ed25519."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.signing_private import ensure_keypair, sign_manifest  # noqa: E402


def main():
    path = ROOT / "updates" / "manifest.json"
    if not path.is_file():
        raise SystemExit(f"Нет файла {path}")
    ensure_keypair()
    data = json.loads(path.read_text(encoding="utf-8"))
    data.pop("signature", None)
    data["signature"] = sign_manifest(data)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    print(f"Подписан: {path}")


if __name__ == "__main__":
    main()
