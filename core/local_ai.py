"""Локальные OpenAI-совместимые AI-серверы (без облака)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from core.config import effective_api_key, normalize_base_url

# Провайдеры, которые работают только на ПК пользователя
LOCAL_PROVIDER_IDS = frozenset({
    "ollama",
    "lmstudio",
    "localai",
    "koboldcpp",
    "llamacpp",
})


def is_local_provider(provider_id: str) -> bool:
    return provider_id in LOCAL_PROVIDER_IDS


def _ollama_root(base_url: str) -> str:
    url = (base_url or "").strip().rstrip("/")
    if url.endswith("/v1"):
        url = url[:-3]
    return url.rstrip("/") or "http://localhost:11434"


def _http_get_json(url: str, *, api_key: str = "", timeout: float = 4.0) -> dict | list:
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def fetch_ollama_models(base_url: str) -> tuple[list[str], str | None]:
    root = _ollama_root(base_url)
    try:
        data = _http_get_json(f"{root}/api/tags", timeout=3.0)
        names = []
        for item in data.get("models") or []:
            name = (item.get("name") or "").strip()
            if name:
                names.append(name)
        if names:
            return sorted(set(names)), None
        return [], "Ollama запущена, но модели не найдены. Выполните: ollama pull llama3.2"
    except urllib.error.URLError as e:
        return [], f"Ollama недоступна ({root}). Установите и запустите Ollama."
    except Exception as e:
        return [], str(e)[:100]


def fetch_openai_compatible_models(base_url: str, api_key: str = "") -> tuple[list[str], str | None]:
    url = normalize_base_url(base_url).rstrip("/") + "/models"
    key = effective_api_key(api_key, base_url, "")
    try:
        data = _http_get_json(url, api_key=key, timeout=4.0)
        names = []
        items = data.get("data") if isinstance(data, dict) else data
        if not isinstance(items, list):
            return [], "Сервер не вернул список моделей (/v1/models)."
        for item in items:
            if isinstance(item, dict):
                mid = (item.get("id") or item.get("name") or "").strip()
                if mid:
                    names.append(mid)
            elif isinstance(item, str) and item.strip():
                names.append(item.strip())
        if names:
            return sorted(set(names)), None
        return [], "Сервер доступен, но модели не загружены."
    except urllib.error.URLError:
        return [], f"Локальный сервер недоступен ({normalize_base_url(base_url)})."
    except Exception as e:
        return [], str(e)[:100]


def fetch_local_models(provider_id: str, base_url: str, api_key: str = "") -> tuple[list[str], str | None]:
    """Список моделей с локального сервера."""
    if provider_id == "ollama":
        return fetch_ollama_models(base_url)
    return fetch_openai_compatible_models(base_url, api_key)
