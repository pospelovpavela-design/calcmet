@echo off
chcp 65001 >nul
echo Сборка EXE для Windows...
cd /d "%~dp0"

pip install pyinstaller

pyinstaller --noconfirm ^
    --name "Metalloemkost" ^
    --windowed ^
    --onefile ^
    --hidden-import "pandas" ^
    --hidden-import "openpyxl" ^
    --hidden-import "docx" ^
    --hidden-import "customtkinter" ^
    --hidden-import "PIL" ^
    --collect-all customtkinter ^
    --collect-all darkdetect ^
    main.py

echo.
echo Готово: dist\Metalloemkost.exe
pause
