# HelpeRP

**HelpeRP** — десктопный оверлей для RP-игроков: база знаний по фракциям, меры и наказания, шаблоны отыгровок, умный поиск и генерация `/me`, `/do` с помощью ИИ.

| | |
|---|---|
| **Версия** | 1.1.0 |
| **Сайт и документация** | https://yeolka-lm.github.io/HelpeRP_Client/ |
| **Обновления** | https://yeolka-lm.github.io/HelpeRP_Client/updates/manifest.json |
| **Лицензия** | Коммерческая (см. [legal/EULA_RU.txt](legal/EULA_RU.txt)) |

---

## Возможности

### База знаний
- Статьи, протоколы и словарь по **11+ фракциям**: МВД, СК, СМП, МЧС, ФСБ, Армия и др.
- **RAG-поиск** — поиск по смыслу, а не только по точному совпадению
- **Wikipedia / Викисловарь** при пустом локальном результате
- Раздел **«Энциклопедия»** с кешем просмотренных статей

### Меры и шаблоны
- **Меры** — УК, КоАП, уровни розыска 1–6, фильтры
- **Шаблоны** — готовые `/me`, `/do`, `/try` **без API-ключа**

### ИИ-отыгровки
- Поддержка OpenAI-совместимых API: **OpenAI, DeepSeek, Groq, OpenRouter, Mistral и другие**
- **Локально без облака:** Ollama, LM Studio, LocalAI, KoboldCpp, llama.cpp
- Несколько **профилей персонажей** для разных RP-героев

### Интерфейс
- Компактный режим поверх игры (`Shift+\`)
- **7 тем оформления** + свой акцент в формате `#hex`
- Плавные анимации и всплывающие уведомления
- Автообновления с проверкой подписи manifest

### Безопасность (v2)
- Лицензии **Ed25519** — приватный ключ хранится только у продавца, а не в exe
- Release-сборка без dev-bypass (`.helperp_dev` не работает в exe)
- Защита от Zip Slip в автообновлении
- Обязательный **sha256** + **Ed25519-подпись** manifest
- API-ключ шифруется **Windows DPAPI** в `settings.json`

---

## Быстрый старт (разработка)

```bash
git clone https://github.com/yeolka-lm/HelpeRP_Client.git
cd HelpeRP_Client
pip install -r requirements.txt

# Режим разработки — лицензия не нужна
type nul > .helperp_dev

py run.py
```

### Горячие клавиши

| Клавиши | Действие |
|---------|----------|
| `Shift+\` | Компактный ↔ развёрнутый режим |
| `Ctrl+Shift+H` | Скрыть / показать окно |
| `Ctrl+F` | Фокус на поиск |
| `↑` / `↓` | Навигация по списку |
| `Esc` | Сброс поиска |

---

## Структура проекта

```
HelpeRP_Client/
├── run.py                 # Точка входа
├── core/                  # Логика: поиск, ИИ, лицензии, обновления
│   ├── licensing.py       # Проверка лицензий (Ed25519)
│   ├── signing_public.py  # Публичный ключ (в exe)
│   ├── rag_search.py      # BM25-поиск
│   ├── ai_client.py       # ИИ-отыгровки
│   └── updates.py         # Проверка обновлений
├── gui/                   # CustomTkinter UI
├── data/                  # JSON-базы фракций, шаблоны, терминология
├── assets/icons/          # Иконки и logo
├── legal/                 # EULA, инструкция продавца
├── docs/                  # Документация (Markdown)
├── website/               # GitHub Pages (лендинг + Docsify)
├── tools/                 # Сборка, ключи, релиз (НЕ для покупателей)
│   ├── build_exe.py       # PyInstaller → dist/HelpeRP.exe
│   ├── release.py         # Релиз: bump + zip + manifest
│   ├── generate_license_key.py
│   └── .license_private.pem  # ⚠ только у продавца, в .gitignore
└── .github/workflows/     # CI: Pages, Release
```

---

## Сборка exe (release)

```bash
pip install -r requirements.txt pyinstaller cryptography

# Один раз — пара Ed25519 ключей
py tools/generate_license_key.py --init-keys

# Сборка (RELEASE_BUILD=True, dev-bypass отключён)
py tools/build_exe.py
```

Результат: `dist/HelpeRP.exe` и `dist/HelpeRP_Release/`

---

## Релиз и обновления

```bash
# Полный релиз: bump версии → exe → zip → подписанный manifest
py tools/release.py --bump patch

# Локальный сервер обновлений (тест)
py tools/serve_updates.py
```

Публикация на GitHub Pages:
1. **Settings → Pages → Source: GitHub Actions**
2. Push в `main` — workflow `.github/workflows/pages.yml` деплоит `website/`

---

## Лицензирование (для продавца)

```bash
py tools/generate_license_key.py --init-keys   # один раз
py tools/generate_license_key.py               # универсальный ключ
py tools/generate_license_key.py --bound ABCD1234  # привязка к ПК
py tools/sign_manifest.py                      # подписать manifest
```

Подробнее: [legal/SELLER_RU.txt](legal/SELLER_RU.txt)

**Не включать в релиз для покупателей:**
- `tools/` и `tools/.license_private.pem`
- `.helperp_dev`
- `legal/LICENSE_KEYS_EXAMPLE.txt`

---

## Настройки

При первом запуске создаётся `settings.json` рядом с exe (или в корне проекта).

Пример: [settings.json.example](settings.json.example)

| Раздел | Описание |
|--------|----------|
| `ai_provider` | OpenAI, deepseek, ollama, lmstudio… |
| `ui.theme` | Тема оформления (helperp, ocean, ember…) |
| `search.rag` | Умный BM25-поиск |
| `characters` | Профили персонажей |
| `updates` | Автопроверка и автоскачивание |

---

## Документация

| | |
|---|---|
| **Онлайн** | [yeolka-lm.github.io/HelpeRP_Client/#/docs/index](https://yeolka-lm.github.io/HelpeRP_Client/#/docs/index) |
| **Локально** | [docs/index.md](docs/index.md) |
| **В приложении** | Сайдбар → Справка |
| **FAQ** | [docs/faq.md](docs/faq.md) |
| **Установка** | [docs/install.md](docs/install.md) |

---

## Зависимости

- Python 3.10+
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — UI
- [OpenAI SDK](https://github.com/openai/openai-python) — совместимые AI API
- [cryptography](https://cryptography.io/) — Ed25519 лицензии и manifest
- `keyboard`, `pydirectinput`, `pyperclip` — хоткеи и отправка в чат

Полный список: [requirements.txt](requirements.txt) · [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)

---

## Разработка

```bash
# Тесты лицензии
py tools/generate_license_key.py 1

# Пересборка иконки
py tools/generate_icon.py

# Терминология Wikipedia
py data/terminology_builder.py
```

---

## Контакты

- **GitHub:** https://github.com/yeolka-lm/HelpeRP_Client
- **Поддержка:** смотрите раздел лицензии и данные продавца в `core/version.py`

© 2026 detigone. Все права защищены.
