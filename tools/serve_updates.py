#!/usr/bin/env python3
"""Локальный HTTP-сервер для тестирования автообновлений."""

from __future__ import annotations

import argparse
import http.server
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description="Локальный сервер обновлений HelpeRP")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--dir", type=Path, default=ROOT / "dist" / "releases")
    args = parser.parse_args()

    publish = args.dir
    publish.mkdir(parents=True, exist_ok=True)

    manifest_src = ROOT / "updates" / "manifest.json"
    if manifest_src.is_file():
        import shutil
        shutil.copy2(manifest_src, publish / "manifest.json")

    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(publish), **kw)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler)

    print(f"Сервер обновлений: http://127.0.0.1:{args.port}/")
    print(f"  manifest → http://127.0.0.1:{args.port}/manifest.json")
    print(f"  Папка: {publish}")
    print("\nВ настройках HelpeRP укажите URL manifest:")
    print(f"  http://127.0.0.1:{args.port}/manifest.json")
    print("\nCtrl+C — остановить")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлено.")


if __name__ == "__main__":
    main()
