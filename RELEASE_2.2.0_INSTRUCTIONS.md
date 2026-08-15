# HelpeRP 2.2.0 - Инструкция по релизу

## Подготовка к релизу

### 1. Проверка версии
Версия уже обновлена до **2.2.0** в `core/version.py`

```python
VERSION = "2.2.0"
```

### 2. Обновление manifest.json
✓ Уже обновлено в `updates/manifest.json` с версией 2.2.0

## Процесс сборки EXE

### Шаг 1: Очистить предыдущие сборки
```bash
cd f:\HelpeRP_Client
rmdir /s /q dist
rmdir /s /q build
del HelpeRP.exe 2>nul
```

### Шаг 2: Собрать EXE
```bash
python tools/build_exe.py
```

Это выполнит:
- ✓ Проверку cryptography
- ✓ Инициализацию ключей подписи
- ✓ Генерацию иконки
- ✓ Установку PyInstaller если нужно
- ✓ Компиляцию в `dist/HelpeRP_Release/HelpeRP.exe`

**Время сборки:** ~5-10 минут

### Шаг 3: Тестирование EXE локально
```bash
dist\HelpeRP_Release\HelpeRP.exe
```

Проверить:
- ✓ Приложение запускается без ошибок
- ✓ Bootstrap показывает установку зависимостей
- ✓ Discord RPC подключается и показывается
- ✓ Все основные функции работают

## Процесс создания распределяемого пакета

### Шаг 4: Создание ZIP архива
```bash
python tools/release.py --version 2.2.0 --build
```

Это создаст:
- `dist/releases/HelpeRP_2.2.0.zip` (~50-100 MB)
- Со всем содержимым из `dist/HelpeRP_Release`

### Шаг 5: Проверка SHA256
```bash
# Windows PowerShell
Get-FileHash dist\releases\HelpeRP_2.2.0.zip -Algorithm SHA256 | Format-List
```

Скопируйте SHA256 хеш и обновите `updates/manifest.json`:
```json
{
    "version": "2.2.0",
    "sha256": "ВСТАВИТЬ_ХЕШ_ЗДЕСЬ",
    "file_size": 52428800,
    ...
}
```

## Публикация на GitHub

### Шаг 6: Создание GitHub Release
1. Перейти на https://github.com/yeolka-lm/HelpeRP_Client/releases
2. Нажать "Create a new release"
3. Заполнить форму:
   - **Tag name:** `v2.2.0`
   - **Release title:** `HelpeRP 2.2.0`
   - **Description:** Содержимое из `CHANGELOG_2.2.0.md`
4. Прикрепить файлы:
   - `dist/releases/HelpeRP_2.2.0.zip`
   - `dist/HelpeRP_Release/HelpeRP.exe` (опционально)
5. Нажать "Publish release"

### Шаг 7: Обновление manifest.json на GitHub Pages
1. Клон/Update GitHub Pages репозитория
2. Скопировать обновленный `updates/manifest.json` в `website/updates/manifest.json`
3. Commit & push:
```bash
git add website/updates/manifest.json
git commit -m "Release 2.2.0: Update manifest with bootstrap and Discord RPC improvements"
git push
```

## Проверка релиза

### Шаг 8: Тестирование загрузки
1. Скачать HelpeRP_2.2.0.zip из GitHub Release
2. Распаковать на чистую машину
3. Запустить HelpeRP.exe и проверить:
   - ✓ Bootstrap установит зависимости
   - ✓ Приложение полностью функционально
   - ✓ Discord RPC работает

### Шаг 9: Тестирование автообновления (опционально)
1. На машине с версией 2.0.1 откройте приложение
2. Проверьте Настройки → О программе
3. Должно предложить обновить до 2.2.0
4. Проверьте, что обновление скачивается и устанавливается

## Финальная проверка списка файлов

Перед релизом убедитесь что в `dist/releases/HelpeRP_2.2.0.zip` содержится:
```
HelpeRP_Release/
├── HelpeRP.exe (основное приложение)
├── core/
│   ├── bootstrap.py ✓ (новый файл)
│   ├── version.py ✓ (v2.2.0)
│   ├── discord_presence.py ✓ (обновлено)
│   └── ...другие модули
├── gui/
│   └── ...все файлы GUI
├── data/
│   ├── templates.json ✓ (v2.0)
│   └── ...другие JSON файлы
├── assets/
│   └── ...иконки и ресурсы
├── docs/
│   └── install.md ✓ (обновлено)
└── settings.json ✓ (обновлено для Discord RPC)
```

## Быстрая команда для полного релиза

Если всё готово, можно сделать так:
```bash
# 1. Собрать
python tools/build_exe.py

# 2. Проверить
dist\HelpeRP_Release\HelpeRP.exe

# 3. Создать ZIP и manifest
python tools/release.py --version 2.2.0 --build

# 4. Получить SHA256 (скопировать значение)
Get-FileHash dist\releases\HelpeRP_2.2.0.zip -Algorithm SHA256

# 5. Обновить manifest вручную или скриптом
# Обновить updates/manifest.json с правильным SHA256

# 6. Закоммитить в git
git add core/version.py updates/manifest.json CHANGELOG_2.2.0.md
git commit -m "Release 2.2.0"
git tag v2.2.0
git push origin main
git push origin v2.2.0
```

## Что было добавлено в 2.2.0

✅ **core/bootstrap.py** - Новый модуль для автоустановки зависимостей
✅ **core/version.py** - Обновлена до 2.2.0
✅ **core/discord_presence.py** - Исправлен Client ID, добавлены timeout и обработка ошибок
✅ **run.py** - Добавлен вызов bootstrap при запуске
✅ **settings.json** - Discord RPC включен по умолчанию с правильным Client ID
✅ **docs/install.md** - Добавлена информация о Discord RPC
✅ **CHANGELOG_2.2.0.md** - Подробный список изменений
✅ **updates/manifest.json** - Обновлен для версии 2.2.0

---

**Дата создания инструкции:** 14 августа 2026
**Версия:** 2.2.0
**Автор:** detigone (HelpeRP Team)
