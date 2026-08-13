"""Пресеты OpenAI-совместимых AI-провайдеров."""

from __future__ import annotations

from core.config import normalize_base_url

PROVIDERS: dict[str, dict] = {
    # --- Локально (без облака и оплаты) ---
    "ollama": {
        "label": "Ollama (локально)",
        "base_url": "http://localhost:11434/v1",
        "default_model": "llama3.2",
        "models": ["llama3.2", "mistral", "qwen2.5", "gemma2", "deepseek-r1:8b"],
        "key_hint": "не нужен",
        "docs": "https://ollama.com/download",
        "setup": "1) Установите Ollama  2) ollama pull llama3.2  3) Проверить API",
        "local": True,
    },
    "lmstudio": {
        "label": "LM Studio (локально)",
        "base_url": "http://localhost:1234/v1",
        "default_model": "local-model",
        "models": [],
        "key_hint": "не нужен",
        "docs": "https://lmstudio.ai",
        "setup": "LM Studio → Local Server → Start Server (порт 1234)",
        "local": True,
    },
    "localai": {
        "label": "LocalAI (локально)",
        "base_url": "http://localhost:8080/v1",
        "default_model": "gpt-4",
        "models": [],
        "key_hint": "не нужен",
        "docs": "https://localai.io",
        "setup": "Docker или бинарник LocalAI на порту 8080",
        "local": True,
    },
    "koboldcpp": {
        "label": "KoboldCpp (локально)",
        "base_url": "http://localhost:5001/v1",
        "default_model": "kobold-model",
        "models": [],
        "key_hint": "не нужен",
        "docs": "https://github.com/LostRuins/koboldcpp",
        "setup": "Запустите KoboldCpp с флагом --openapi (порт 5001)",
        "local": True,
    },
    "llamacpp": {
        "label": "llama.cpp server (локально)",
        "base_url": "http://127.0.0.1:8080/v1",
        "default_model": "gguf-model",
        "models": [],
        "key_hint": "не нужен",
        "docs": "https://github.com/ggerganov/llama.cpp",
        "setup": "llama-server --port 8080 --model model.gguf",
        "local": True,
    },
    # --- Облачные API ---
    "openai": {
        "label": "OpenAI (облако)",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1", "gpt-3.5-turbo"],
        "key_hint": "sk-…",
        "docs": "https://platform.openai.com/api-keys",
        "local": False,
    },
    "deepseek": {
        "label": "DeepSeek (облако)",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "key_hint": "sk-…",
        "docs": "https://platform.deepseek.com/api_keys",
        "local": False,
    },
    "groq": {
        "label": "Groq (облако)",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ],
        "key_hint": "gsk_…",
        "docs": "https://console.groq.com/keys",
        "local": False,
    },
    "openrouter": {
        "label": "OpenRouter (облако)",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "openai/gpt-4o-mini",
        "models": [
            "openai/gpt-4o-mini",
            "deepseek/deepseek-chat",
            "google/gemini-2.0-flash-001",
            "anthropic/claude-3.5-sonnet",
            "meta-llama/llama-3.3-70b-instruct",
        ],
        "key_hint": "sk-or-…",
        "docs": "https://openrouter.ai/keys",
        "local": False,
    },
    "mistral": {
        "label": "Mistral AI (облако)",
        "base_url": "https://api.mistral.ai/v1",
        "default_model": "mistral-small-latest",
        "models": ["mistral-small-latest", "mistral-large-latest", "codestral-latest"],
        "key_hint": "…",
        "docs": "https://console.mistral.ai/api-keys",
        "local": False,
    },
    "together": {
        "label": "Together AI (облако)",
        "base_url": "https://api.together.xyz/v1",
        "default_model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "models": [
            "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
            "Qwen/Qwen2.5-72B-Instruct-Turbo",
        ],
        "key_hint": "…",
        "docs": "https://api.together.xyz/settings/api-keys",
        "local": False,
    },
    "yandex": {
        "label": "YandexGPT (облако)",
        "base_url": "https://llm.api.cloud.yandex.net/v1",
        "default_model": "yandexgpt-lite",
        "models": ["yandexgpt-lite", "yandexgpt", "yandexgpt-32k"],
        "key_hint": "Api-Key …",
        "docs": "https://yandex.cloud/ru/docs/foundation-models/",
        "local": False,
    },
    "custom": {
        "label": "Свой сервер",
        "base_url": "",
        "default_model": "",
        "models": [],
        "key_hint": "ключ вашего сервера",
        "docs": "",
        "local": False,
    },
}

PROVIDER_IDS = list(PROVIDERS.keys())
PROVIDER_LABELS = [PROVIDERS[k]["label"] for k in PROVIDER_IDS]
LOCAL_LABELS = [PROVIDERS[k]["label"] for k in PROVIDER_IDS if PROVIDERS[k].get("local")]


def provider_id_by_label(label: str) -> str:
    for pid, p in PROVIDERS.items():
        if p["label"] == label:
            return pid
    return "custom"


def provider_label(provider_id: str) -> str:
    return PROVIDERS.get(provider_id, PROVIDERS["custom"])["label"]


def detect_provider(base_url: str) -> str:
    url = normalize_base_url(base_url).rstrip("/").lower()
    if not url or url == "https://api.openai.com/v1":
        return "openai"
    for pid, p in PROVIDERS.items():
        if pid == "custom":
            continue
        preset = normalize_base_url(p["base_url"]).rstrip("/").lower()
        if url == preset or url.startswith(preset):
            return pid
    if "localhost" in url or "127.0.0.1" in url:
        return "custom"
    return "custom"


def provider_defaults(provider_id: str) -> dict:
    p = PROVIDERS.get(provider_id) or PROVIDERS["custom"]
    return {
        "base_url": p["base_url"],
        "model": p["default_model"],
        "models": list(p.get("models") or []),
        "local": bool(p.get("local")),
    }
