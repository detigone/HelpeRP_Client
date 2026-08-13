# Обновления HelpeRP

## Для пользователя (всё автоматически)

1. При запуске HelpeRP проверяет `manifest.json` на сервере
2. Если есть новая версия — показывается уведомление
3. Пакет **скачивается автоматически** (если включено в настройках)
4. Нажмите **«Установить автоматически»** — программа перезапустится с новой версией

**Настройки → Обновления:**

| Опция | Описание |
|-------|----------|
| Проверять автоматически | При запуске и каждые 24 ч |
| Скачивать автоматически | Фоновая загрузка zip-пакета |
| Проверить сейчас | Ручная проверка |

## Для разработчика / продавца (одна команда)

```bash
# Новый релиз: поднять patch-версию, собрать exe, zip, manifest с sha256
py tools/release.py --bump patch

# С changelog из файла
py tools/release.py --bump minor --changelog-file CHANGELOG.txt

# Только пересобрать manifest для текущей версии
py tools/release.py --skip-build
```

Результат:

```
dist/releases/HelpeRP_1.2.0.zip   ← загрузить на хостинг
updates/manifest.json             ← загрузить по UPDATE_MANIFEST_URL
dist/releases/manifest.json       ← копия для публикации
```

### Публикация

1. Укажите `UPDATE_MANIFEST_URL` в `core/version.py`
2. Загрузите `HelpeRP_X.Y.Z.zip` и `manifest.json` на CDN/сервер
3. Пользователи получат обновление автоматически

### Локальный тест

```bash
# Терминал 1 — релиз с локальным URL
py tools/release.py --bump patch --download-url http://127.0.0.1:8765/HelpeRP_1.2.0.zip

# Терминал 2 — локальный сервер
py tools/serve_updates.py

# В HelpeRP: Настройки → URL manifest → http://127.0.0.1:8765/manifest.json
```

## Формат manifest.json

```json
{
  "version": "1.2.0",
  "released": "2026-09-01",
  "title": "HelpeRP 1.2.0",
  "download_url": "https://your-site.com/releases/HelpeRP_1.2.0.zip",
  "sha256": "abc123…",
  "file_size": 12345678,
  "changelog": "• …",
  "required": false
}
```

Поле `sha256` проверяется перед установкой — защита от повреждённых загрузок.

## GitHub Actions

При push тега `v*` workflow `.github/workflows/release.yml` автоматически:

1. Собирает exe
2. Создаёт zip и manifest
3. Публикует GitHub Release

## Офлайн

Без интернета приложение работает как обычно. Проверка обновлений пропускается.
