#!/bin/bash
# ──────────────────────────────────────────────────────────────
#  Локальная сборка iOS-приложения MetalCalc
#  Установка на iPhone через Xcode (шнурок)
# ──────────────────────────────────────────────────────────────
set -e

# kivy-ios не поддерживает Python 3.13 — нужен Python 3.11
CONDA_ENV="kivy-ios"
if conda env list 2>/dev/null | grep -q "^$CONDA_ENV "; then
    # Активируем среду внутри скрипта
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate "$CONDA_ENV"
else
    echo -e "\033[0;31m✗ Conda-среда '$CONDA_ENV' не найдена.\033[0m"
    echo ""
    echo "Создайте её один раз:"
    echo "  conda create -n $CONDA_ENV python=3.11 -y"
    echo "  conda activate $CONDA_ENV"
    echo "  pip install cython kivy-ios"
    echo ""
    echo "Затем повторите: ./build_ios_local.sh"
    exit 1
fi
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$SCRIPT_DIR/kivy-ios-build"
APP_NAME="MetalCalc"
XCODEPROJ="$WORKSPACE/${APP_NAME}-ios/${APP_NAME}.xcodeproj"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}▶ $*${NC}"; }
success() { echo -e "${GREEN}✓ $*${NC}"; }
warn()    { echo -e "${YELLOW}⚠ $*${NC}"; }
fail()    { echo -e "${RED}✗ $*${NC}"; exit 1; }

echo ""
echo "══════════════════════════════════════════════════════"
echo "   MetalCalc — Сборка и установка на iPhone"
echo "══════════════════════════════════════════════════════"
echo ""

# ── 1. Проверка Xcode ─────────────────────────────────────
info "Проверка Xcode..."
if ! xcodebuild -version &>/dev/null; then
    fail "Xcode не установлен!\n\nУстановите Xcode из App Store:\n  https://apps.apple.com/app/xcode/id497799835\n\nПосле установки запустите:\n  sudo xcode-select -s /Applications/Xcode.app/Contents/Developer\n  sudo xcodebuild -license accept"
fi
XCODE_VER=$(xcodebuild -version | head -1)
success "$XCODE_VER"

# ── 2. Brew-зависимости ───────────────────────────────────
info "Проверка brew-зависимостей..."
BREW_PKGS=(autoconf automake libtool pkg-config cmake)
for pkg in "${BREW_PKGS[@]}"; do
    if ! brew list "$pkg" &>/dev/null; then
        warn "Устанавливаю $pkg..."
        brew install "$pkg"
    fi
done
success "Системные зависимости OK"

# ── 3. Python-зависимости ─────────────────────────────────
info "Проверка Python-зависимостей..."
if ! python3 -c "import cython" &>/dev/null; then
    warn "Устанавливаю cython..."
    pip3 install cython
fi
if ! command -v toolchain &>/dev/null; then
    warn "Устанавливаю kivy-ios..."
    pip3 install kivy-ios
fi
success "Python-зависимости OK"

# ── 4. Сборка Kivy для iOS (только если ещё не собран) ───
mkdir -p "$WORKSPACE"
if [ ! -d "$WORKSPACE/dist/lib/python3.11" ]; then
    info "Компиляция Kivy для iOS (первый раз ~60 мин, далее секунды)..."
    cd "$WORKSPACE"
    toolchain build python3 kivy
    success "Kivy для iOS собран"
else
    success "Kivy для iOS уже собран — пропуск"
fi

# ── 5. Создание / обновление Xcode-проекта ───────────────
info "Создание Xcode-проекта..."
cd "$WORKSPACE"
if [ -d "${APP_NAME}-ios" ]; then
    warn "Проект уже существует — обновление..."
    toolchain update "${APP_NAME}-ios"
else
    toolchain create "$APP_NAME" "$SCRIPT_DIR"
fi
success "Xcode-проект: $XCODEPROJ"

# ── 6. Открыть в Xcode ───────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════"
echo -e "${GREEN}  Готово! Открываю Xcode...${NC}"
echo "══════════════════════════════════════════════════════"
echo ""
echo "  Дальнейшие шаги в Xcode:"
echo "  1. Подключите iPhone к Mac шнурком"
echo "  2. Signing & Capabilities → Team: выберите ваш Apple ID"
echo "     (Xcode → Settings → Accounts → + → Apple ID)"
echo "  3. Bundle Identifier: поменяйте на уникальный, напр.:"
echo "     ru.pospelov.metalcalc"
echo "  4. Выберите ваш iPhone в списке устройств (вверху)"
echo "  5. Cmd+R — сборка и установка"
echo "  6. На телефоне: Настройки → Основные → VPN и управление"
echo "     устройством → Доверять [ваш Apple ID]"
echo ""

open "$XCODEPROJ"
