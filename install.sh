#!/usr/bin/env bash
#
# Сборка и установка AirGuard.
#   1. Компилирует Swift-коллектор и упаковывает его в .app-бандл
#      (бандл с Info.plist нужен, чтобы macOS дала доступ к геолокации).
#   2. Ad-hoc подписывает бандл.
#   3. Создаёт виртуальное окружение Python и ставит зависимости.
#
# Запуск:  ./install.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD="$ROOT/build"
APP="$BUILD/AirGuardScanner.app"
SRC="$ROOT/src/collector"

echo "==> AirGuard: сборка"

# --- 0. Проверки окружения ---------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
    echo "Ошибка: нет python3." >&2
    exit 1
fi

# --- 1. Компиляция Swift (необязательно) -------------------------------------
# Нативный коллектор даёт имена сетей и MAC. Если swiftc отсутствует или
# сборка не удалась (например, из-за рассинхрона Command Line Tools), это НЕ
# критично: утилита перейдёт на запасной сбор через system_profiler.
NATIVE_OK=0
if command -v swiftc >/dev/null 2>&1; then
    echo "==> Компилирую Swift-коллектор"
    mkdir -p "$APP/Contents/MacOS"
    if swiftc -O \
        -framework CoreWLAN -framework CoreLocation -framework Foundation \
        -o "$APP/Contents/MacOS/AirGuardScanner" \
        "$SRC"/Sources/*.swift 2>/dev/null; then
        cp "$SRC/Info.plist" "$APP/Contents/Info.plist"
        codesign --force --sign - "$APP" 2>/dev/null || true
        NATIVE_OK=1
        echo "    нативный коллектор собран."
    else
        rm -rf "$APP"
        echo "    не удалось собрать Swift (возможно, повреждены Command Line Tools)."
        echo "    Ничего страшного — утилита будет работать в запасном режиме."
    fi
else
    echo "==> swiftc не найден — пропускаю нативный коллектор (запасной режим)."
fi

# --- 2. Python-окружение -----------------------------------------------------
echo "==> Настраиваю Python-окружение"
if [ ! -d "$ROOT/.venv" ]; then
    python3 -m venv "$ROOT/.venv"
fi
# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -e "$ROOT"

# --- 5. Проверка nmap (для режима --deep) ------------------------------------
if ! command -v nmap >/dev/null 2>&1; then
    echo "Подсказка: для режима --deep установи nmap: brew install nmap"
fi

echo ""
echo "==> Готово."
echo "    Активируй окружение:   source .venv/bin/activate"
echo "    Запусти аудит:         python -m airguard --scan"
echo "    С HTML-отчётом:        python -m airguard --scan --report report.html"
echo ""
echo "    При первом запуске macOS спросит доступ к геолокации — разреши,"
echo "    иначе имена сетей и MAC будут скрыты системой."
