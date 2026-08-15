# Обновление иконок Tabler Icons

## 🚀 Быстрый старт

### Шаг 1: Установить зависимость для конвертации SVG → PNG

```bash
pip install cairosvg
```

Если `cairosvg` не установится (требует системные библиотеки), используйте альтернативный вариант:

```bash
# Windows (с choco)
choco install librsvg

# Linux (Ubuntu/Debian)
sudo apt-get install librsvg2-bin

# macOS (с brew)
brew install librsvg
```

### Шаг 2: Запустить скрипт скачивания

```bash
python tools/download_tabler_icons.py
```

Скрипт:
1. ✓ Удалит старые иконки из `assets/icons/` (кроме logo.png и logo.ico)
2. ✓ Скачает новые иконки из [Tabler Icons](https://tabler-icons.io/) в формате SVG
3. ✓ Конвертирует SVG → PNG (24×24 пиксели)
4. ✓ Поместит их в `assets/icons/`

### Шаг 3: Перезагрузить приложение

Все новые иконки будут загружены автоматически при запуске.

## 📋 Таблица иконок

Скрипт загружает следующие иконки из Tabler:

### Фракции
| Локальное имя | Tabler иконка | Использование |
|---------------|---------------|---|
| logo.png | brand-github | Логотип, "Все базы" |
| rules.png | book-2 | Законодательство |
| moderator.png | shield-check | МВД |
| admin.png | crown | ФСБ |
| editor.png | search | СК |
| management.png | briefcase | Прокуратура |
| star.png | star | Росгвардия |
| owner.png | lock | ФСИН |
| fire.png | flame | МЧС |
| support.png | headphones | СМП |
| web.png | world | СМИ |
| developer.png | code | Армия |
| punishment.png | gavel | Преступность |

### Интерфейс
| Локальное имя | Tabler иконка | Использование |
|---------------|---------------|---|
| home.png | home | Главная страница |
| copy.png | copy | Копирование |
| ai.png | brain | AI ассистент |
| frequent.png | bolt | Часто используемое |
| settings.png | settings | Настройки |
| warning.png | alert-triangle | Предупреждения |
| expand.png | chevron-down | Раскрыть |
| collapse.png | chevron-up | Свернуть |

## 🔧 Ручное добавление иконок

Если нужна другая иконка из Tabler:

1. Найдите иконку на [Tabler Icons](https://tabler-icons.io/)
2. Добавьте её в словарь `TABLER_ICONS_MAP` в `tools/download_tabler_icons.py`:
   ```python
   TABLER_ICONS_MAP = {
       "my_icon": "tabler-icon-name",
   }
   ```
3. Запустите скрипт ещё раз

## 📦 Размеры иконок

- **Иконки интерфейса**: 24×24 px (по умолчанию)
- **Фракции**: 22 px (настраивается в коде)
- **Логотип**: 256×256 px (logo.png + logo.ico)

Если нужны другие размеры, отредактируйте переменную `ICON_SIZE` в скрипте.

## ⚠️ Возможные проблемы

### Ошибка: "cairosvg не установлен"
**Решение:** SVG файлы останутся в `assets/icons/`, но приложение не сможет их загрузить. Установите cairosvg согласно инструкциям выше.

### Ошибка: "не удалось скачать иконку"
**Причины:**
- Проблема с интернетом
- GitHub недоступен
- Иконка удалена/переименована в Tabler

**Решение:** Попробуйте скачать вручную с https://github.com/tabler/tabler-icons/tree/main/icons/outline

### Иконки не обновились в приложении
**Решение:** Очистите кеш PNG:
1. Закройте приложение
2. Удалите `assets/icons/*.png`
3. Запустите скрипт ещё раз
4. Перезагрузите приложение

## 🌐 Источник

- **Иконки**: https://tabler-icons.io/
- **GitHub репо**: https://github.com/tabler/tabler-icons
- **Лицензия**: Tabler Icons распространяются под лицензией MIT

## ✅ Проверка успеха

После запуска скрипта должно быть:
- Минимум 25+ PNG файлов в `assets/icons/`
- Иконки размером 24×24 пиксели
- Файлы logo.png и logo.ico остаются нетронутыми
- Нет SVG файлов (если cairosvg установлен)

```bash
# Проверить количество иконок
ls assets/icons/*.png | wc -l
```

Должно быть примерно 28-30 файлов (иконки + logo.png + logo.ico).
