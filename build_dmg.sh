#!/bin/bash
# Сборка DMG для macOS
set -e
cd "$(dirname "$0")"

echo "Установка зависимостей..."
python3 -m venv .venv_build 2>/dev/null || true
source .venv_build/bin/activate 2>/dev/null || true
pip install pyinstaller customtkinter pandas openpyxl python-docx 2>/dev/null || true
export PYINSTALLER_CONFIG_DIR="$(pwd)/.pyinstaller"
mkdir -p .pyinstaller

echo "Сборка приложения (macOS .app)..."
pyinstaller --noconfirm \
    --workpath build \
    --specpath . \
    --distpath dist \
    --name "Metalloemkost" \
    --windowed \
    --onedir \
    --hidden-import "pandas" \
    --hidden-import "openpyxl" \
    --hidden-import "docx" \
    --hidden-import "customtkinter" \
    --hidden-import "PIL" \
    --collect-all customtkinter \
    --collect-all darkdetect \
    main.py

echo "Создание DMG..."
mkdir -p dist/dmg_source
cp -R dist/Metalloemkost.app dist/dmg_source/ 2>/dev/null || cp -R dist/Metalloemkost dist/dmg_source/Metalloemkost.app
cd dist/dmg_source
if hdiutil create -volname "Металлоемкость" -srcfolder . -ov -format UDZO "../Металлоемкость.dmg" 2>/dev/null; then
    echo "Готово: dist/Металлоемкость.dmg"
else
    echo "hdiutil недоступен. Создаю ZIP-архив..."
    cd ..
    zip -r Металлоемкость_macOS.zip Metalloemkost.app
    echo "Готово: dist/Металлоемкость_macOS.zip (распакуйте и запустите Metalloemkost.app)"
fi
cd ../..
