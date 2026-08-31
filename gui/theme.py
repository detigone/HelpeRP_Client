"""Единая тема оформления HelpeRP — переработанная v2."""

# === ЦВЕТА (Dark-first, тёмно-синяя база с яркими акцентами) ===

# Фоны — слоистая иерархия
BG_ROOT = "#0a0c10"          # Главный фон окна
BG_SIDEBAR = "#0f1218"       # Боковая панель
BG_PANEL = "#141820"         # Панель списка / детали
BG_CARD = "#1b202a"          # Карточки, кнопки, инпуты
BG_ELEVATED = "#202632"      # Всплывающие элементы (dropdown, toast)
BG_HOVER = "#262e3c"         # Hover состояние
BG_SELECTED = "#2d3848"      # Активное/выбранное
BG_INPUT = "#1e2430"         # Поля ввода

# Границы
BORDER = "#2a3342"           # Основная граница
BORDER_LIGHT = "#3a4558"     # Тонкая граница (разделители)
BORDER_ACCENT = "#4a9eff"    # Граница акцента

# Текст — четкая иерархия
TEXT_PRIMARY = "#f1f3f6"     # Заголовки, основной текст
TEXT_SECONDARY = "#a8b2c4"   # Вторичный текст, подписи
TEXT_MUTED = "#6b7a90"       # Подсказки, мета-информация
TEXT_DISABLED = "#4a5568"    # Отключенные элементы
TEXT_ON_ACCENT = "#ffffff"   # Текст на акцентном фоне

# Акценты (фракционные цвета будут переопределять DEFAULT_ACCENT)
DEFAULT_ACCENT = "#4a9eff"
DEFAULT_ACCENT_HOVER = "#6ab0ff"
DEFAULT_ACCENT_SOFT = "#1e3a5f"  # Для фонов с оттенком акцента

# Семантические цвета
SUCCESS = "#22c55e"
SUCCESS_SOFT = "#14532d"
WARNING = "#f59e0b"
WARNING_SOFT = "#78350f"
ERROR = "#ef4444"
ERROR_SOFT = "#7f1d1d"
INFO = "#8b5cf6"
INFO_SOFT = "#3b0764"

# === ТИПОГРАФИКА ===
FONT_FAMILY = "Segoe UI"
FONT_FAMILY_MONO = "Cascadia Code"

FONT_DISPLAY = ("Segoe UI", 28, "bold")      # Крупный заголовок (бренд)
FONT_TITLE = ("Segoe UI", 20, "bold")        # Заголовки страниц
FONT_HEADING = ("Segoe UI", 14, "bold")      # Заголовки секций
FONT_SUBHEADING = ("Segoe UI", 12, "bold")   # Подзаголовки
FONT_BODY = ("Segoe UI", 13)                 # Основной текст
FONT_BODY_SM = ("Segoe UI", 12)              # Мелкий текст
FONT_SMALL = ("Segoe UI", 11)                # Мелкие подписи
FONT_TINY = ("Segoe UI", 10)                 # Очень мелкий текст
FONT_MONO = ("Cascadia Code", 11)            # Моноширинный
FONT_MONO_SM = ("Cascadia Code", 10)         # Малый моно

# === РАЗМЕРЫ И ОТСТУПЫ ===
RADIUS_XS = 4
RADIUS_SM = 8
RADIUS_MD = 10
RADIUS_LG = 14
RADIUS_XL = 18
RADIUS_FULL = 9999

# Backward compatibility
RADIUS = RADIUS_MD
RADIUS_LG_COMPAT = RADIUS_LG

PAD_XS = 4
PAD_SM = 8
PAD_MD = 12
PAD_LG = 16
PAD_XL = 24
PAD_2XL = 32

# Backward compatibility
PAD = PAD_LG
PAD_SM_COMPAT = PAD_SM
PAD_XS_COMPAT = PAD_XS

GAP_XS = 4
GAP_SM = 8
GAP_MD = 12
GAP_LG = 16
GAP_XL = 24

ICON_XS = 14
ICON_SM = 18
ICON_MD = 22
ICON_LG = 28
ICON_XL = 36

# Backward compatibility
EXPANDED_SIZE = (1280, 800)
COMPACT_SIZE = (800, 64)

# === ТЕНИ И ЭФФЕКТЫ (для будущего использования) ===
SHADOW_SM = "0 1px 2px rgba(0,0,0,0.3)"
SHADOW_MD = "0 4px 8px rgba(0,0,0,0.4)"
SHADOW_LG = "0 8px 24px rgba(0,0,0,0.5)"

# === АНИМАЦИИ ===
ANIM_FAST = 120
ANIM_NORMAL = 200
ANIM_SLOW = 300