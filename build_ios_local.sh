#!/bin/bash
# ──────────────────────────────────────────────────────────────
#  Локальная сборка iOS-приложения MetalCalc
#  Установка на iPhone через Xcode (шнурок)
# ──────────────────────────────────────────────────────────────
set -e

# kivy-ios не поддерживает Python 3.13; используем локальный venv на доступном Python 3.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv-ios"
PYTHON_BIN="$(command -v python3.11 || command -v python3)"
if [ -z "$PYTHON_BIN" ]; then
    echo -e "\033[0;31m✗ Не найден python3 или python3.11.\033[0m"
    echo "Установите Python 3 и повторите: ./build_ios_local.sh"
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip --version >/dev/null

WORKSPACE="$SCRIPT_DIR/kivy-ios-build"
APP_NAME="metalcalc"
APP_DISPLAY_NAME="MetalCalc"
BUNDLE_ID="${BUNDLE_ID:-ru.pospelov.metalcalc}"
XCODEPROJ="$WORKSPACE/${APP_NAME}-ios/${APP_NAME}.xcodeproj"

if [ -d "/Applications/Xcode.app" ]; then
    export DEVELOPER_DIR="/Applications/Xcode.app/Contents/Developer"
fi

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}▶ $*${NC}"; }
success() { echo -e "${GREEN}✓ $*${NC}"; }
warn()    { echo -e "${YELLOW}⚠ $*${NC}"; }
fail()    { echo -e "${RED}✗ $*${NC}"; exit 1; }

echo ""
echo "══════════════════════════════════════════════════════"
echo "   $APP_DISPLAY_NAME — Сборка и установка на iPhone"
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
if ! python -c "import Cython" &>/dev/null; then
    warn "Устанавливаю cython в $VENV_DIR..."
    python -m pip install cython
fi
if ! command -v toolchain &>/dev/null; then
    warn "Устанавливаю kivy-ios в $VENV_DIR..."
    python -m pip install kivy-ios
fi
SDL2_MIXER_RECIPE="$(python -c 'import pathlib, kivy_ios; print(pathlib.Path(kivy_ios.__file__).parent / "recipes" / "sdl2_mixer" / "__init__.py")')"
if [ -f "$SDL2_MIXER_RECIPE" ] && ! grep -q "from os.path import join" "$SDL2_MIXER_RECIPE"; then
    warn "Исправляю recipe sdl2_mixer в установленном kivy-ios..."
    perl -0pi -e 's/from kivy_ios\.toolchain import Recipe, shprint\n/from kivy_ios.toolchain import Recipe, shprint\nfrom os.path import join\n/' "$SDL2_MIXER_RECIPE"
fi
if [ -f "$SDL2_MIXER_RECIPE" ] && grep -q -- "-derivedDataPath" "$SDL2_MIXER_RECIPE"; then
    warn "Удаляю несовместимый -derivedDataPath из recipe sdl2_mixer..."
    perl -0pi -e 's/\s*"-derivedDataPath", join\(self\.get_build_dir\(plat\), "DerivedData"\),\n//' "$SDL2_MIXER_RECIPE"
fi
success "Python-зависимости OK"

# ── 4. Сборка Kivy для iOS (только если ещё не собран) ───
mkdir -p "$WORKSPACE"
if [ ! -d "$WORKSPACE/dist/lib/python3.11" ]; then
    info "Компиляция Kivy для iOS (первый раз ~60 мин, далее секунды)..."
    cd "$WORKSPACE"
    mkdir -p "$WORKSPACE/xcode-home"
    HOME="$WORKSPACE/xcode-home" toolchain build python3 kivy --platform iphoneos-arm64 --platform iphonesimulator-arm64
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
XCODEPROJ="$(find "$WORKSPACE/${APP_NAME}-ios" -maxdepth 1 -name "*.xcodeproj" -print -quit)"
if [ -z "$XCODEPROJ" ]; then
    fail "Xcode-проект не найден в $WORKSPACE/${APP_NAME}-ios"
fi
PBXPROJ="$XCODEPROJ/project.pbxproj"
if [ -f "$PBXPROJ" ]; then
    info "Настройка проекта под iPhone..."
    perl -0pi -e 's/TARGETED_DEVICE_FAMILY = "[^"]+";/TARGETED_DEVICE_FAMILY = 1;/g; s/TARGETED_DEVICE_FAMILY = [^;]+;/TARGETED_DEVICE_FAMILY = 1;/g' "$PBXPROJ"
    perl -0pi -e 's/IPHONEOS_DEPLOYMENT_TARGET = [^;]+;/IPHONEOS_DEPLOYMENT_TARGET = 15.0;/g' "$PBXPROJ"
    perl -0pi -e "s#rsync -av .*?\\\"$SCRIPT_DIR\\\"/ \\\"\\\$PROJECT_DIR\\\"/YourApp#rsync -av --delete --delete-excluded --exclude '.git/' --exclude '.github/' --exclude '.venv/' --exclude '.venv-ios/' --exclude '.pytest_cache/' --exclude '__pycache__/' --exclude 'kivy-ios-build/' \\\"$SCRIPT_DIR\\\"/ \\\"\\\$PROJECT_DIR\\\"/YourApp#g" "$PBXPROJ"
fi
INFO_PLIST="$(find "$(dirname "$XCODEPROJ")" -maxdepth 1 -name "*-Info.plist" -print -quit)"
if [ -n "$INFO_PLIST" ]; then
    /usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier $BUNDLE_ID" "$INFO_PLIST" 2>/dev/null || true
    /usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName $APP_DISPLAY_NAME" "$INFO_PLIST" 2>/dev/null || true
    /usr/libexec/PlistBuddy -c "Set :CFBundleName $APP_DISPLAY_NAME" "$INFO_PLIST" 2>/dev/null || true
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
echo "  3. Bundle Identifier уже задан: $BUNDLE_ID"
echo "     Если Xcode ругается на него — задайте другой уникальный"
echo "  4. Выберите ваш iPhone в списке устройств (вверху)"
echo "  5. Cmd+R — сборка и установка"
echo "  6. На телефоне: Настройки → Основные → VPN и управление"
echo "     устройством → Доверять [ваш Apple ID]"
echo ""

open "$XCODEPROJ"
