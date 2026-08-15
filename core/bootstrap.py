"""Инициализация зависимостей при запуске EXE."""

import subprocess
import sys
from pathlib import Path

# Требуемые пакеты
REQUIRED_PACKAGES = [
    "customtkinter>=5.2.0",
    "Pillow>=10.0.0",
    "keyboard>=0.13.5",
    "openai>=1.0.0",
    "pydirectinput>=1.0.4",
    "pyperclip>=1.8.2",
    "cryptography>=42.0.0",
    "pypresence>=4.3.0",
]

# Опциональные пакеты (не блокируют запуск если не установлены)
OPTIONAL_PACKAGES = [
    "requests>=2.31.0",  # Для загрузки обновлений
    "chromadb>=0.4.0",   # Для RAG поиска (если включен)
    "langchain>=0.1.0",  # Для работы с LLM
]


def _check_package(package_name: str) -> bool:
    """Проверить установлен ли пакет."""
    try:
        base_name = package_name.split(">=")[0].split("==")[0].split("<")[0].split(">")[0]
        __import__(base_name.replace("-", "_"))
        return True
    except ImportError:
        return False


def _install_package(package: str) -> bool:
    """Установить пакет через pip."""
    try:
        print(f"  Установка {package}...", end=" ", flush=True)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", package],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("✓")
        return True
    except Exception as e:
        print(f"✗ ({e})")
        return False


def ensure_dependencies() -> bool:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    """Проверить и установить обязательные зависимости."""
    missing = [pkg for pkg in REQUIRED_PACKAGES if not _check_package(pkg)]

    if not missing:
        return True

    print("\n[Bootstrap] Проверка зависимостей...")
    print(f"[Bootstrap] Не найдено пакетов: {len(missing)}\n")

    installed = 0
    for package in missing:
        if _install_package(package):
            installed += 1

    print(f"\n[Bootstrap] Установлено: {installed}/{len(missing)}")

    if installed < len(missing):
        print("[Bootstrap] ⚠ Некоторые пакеты не установились.")
        print(f"[Bootstrap] Попробуйте вручную: pip install -r requirements.txt")
        return False

    print("[Bootstrap] ✓ Все зависимости установлены\n")
    return True


def ensure_optional_dependencies() -> None:
    """Тихо установить опциональные пакеты."""
    missing = [pkg for pkg in OPTIONAL_PACKAGES if not _check_package(pkg)]
    if not missing:
        return

    print("[Bootstrap] Установка опциональных пакетов...", flush=True)
    for package in missing:
        _install_package(package)
    print("[Bootstrap] ✓ Опциональные пакеты обновлены\n")


def check_data_files() -> None:
    """Проверить наличие необходимых файлов данных."""
    data_dir = Path(__file__).resolve().parent.parent / "data"
    required_files = [
        "templates.json",
        "legislation_rf.json",
        "mvd.json",
    ]

    missing = [f for f in required_files if not (data_dir / f).exists()]
    if missing:
        print(f"[Bootstrap] ⚠ Отсутствуют файлы: {', '.join(missing)}")
        print(f"[Bootstrap] Переустановите приложение через exe")


def run_bootstrap() -> bool:
    """Запустить полную инициализацию."""
    try:
        # 1. Проверить обязательные зависимости
        if not ensure_dependencies():
            print("[Bootstrap] ⚠ Приложение может работать нестабильно\n")

        # 2. Установить опциональные пакеты (фоном)
        try:
            ensure_optional_dependencies()
        except Exception as e:
            print(f"[Bootstrap] Ошибка при установке опциональных: {e}")

        # 3. Проверить файлы данных
        check_data_files()

        return True
    except Exception as e:
        print(f"[Bootstrap] Критическая ошибка: {e}")
        return False
