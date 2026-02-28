@echo off
REM ============================================================
REM  MetalCalc Suite v2.0 — сборка Windows EXE
REM  Запускать на Windows + Python 3.11-3.13
REM  Результат: dist\MetalCalcSuite.exe
REM ============================================================

echo Установка зависимостей...
pip install customtkinter pillow darkdetect packaging pyinstaller

echo.
echo Сборка MetalCalc Suite (все три калькулятора)...
pyinstaller --noconfirm --clean launcher_windows.spec

echo.
if exist "dist\MetalCalcSuite.exe" (
    echo  OK  dist\MetalCalcSuite.exe
) else (
    echo  ОШИБКА: файл не найден
)
pause
