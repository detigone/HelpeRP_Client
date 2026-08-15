"""Единая кэширующая загрузка JSON-баз HelpeRP.

Избавляет от дублирования паттерна «глобальный кэш + ленивая загрузка»,
который повторялся в core/measures.py и core/templates.py.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache


@lru_cache(maxsize=64)
def _read_json_cached(path: str) -> object:
    """Прочитать JSON-файл с кэшем результата."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[json_loader] Ошибка чтения {path}: {e}")
        return None


def load_json(path: str) -> object:
    """Загрузить JSON-файл (кэшируется по пути). Возвращает None при ошибке."""
    return _read_json_cached(path)


def load_json_list(path: str) -> list[dict]:
    """Загрузить JSON-файл и вернуть список записей (или пустой список)."""
    data = _read_json_cached(path)
    return data if isinstance(data, list) else []


def clear_cache() -> None:
    """Сбросить кэш JSON (полезно после обновления баз)."""
    _read_json_cached.cache_clear()