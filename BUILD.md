# Сборка DMG и EXE

## macOS (DMG)

```bash
./build_dmg.sh
```

Результат:
- `dist/Металлоемкость.dmg` — если hdiutil доступен
- `dist/Металлоемкость_macOS.zip` — приложение в архиве (распаковать и запустить Metalloemkost.app)

Приложение также доступно в `dist/Metalloemkost.app`.

### Создание DMG вручную

Если скрипт не создал DMG:

```bash
mkdir -p dist/dmg_source
cp -R dist/Metalloemkost.app dist/dmg_source/
cd dist/dmg_source
hdiutil create -volname "Металлоемкость" -srcfolder . -ov -format UDZO "../Металлоемкость.dmg"
```

---

## Windows (EXE)

**Требуется Windows** — PyInstaller не поддерживает кросс-компиляцию.

1. Установите Python 3.10+ и зависимости:
   ```
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. Запустите сборку:
   ```
   build_exe.bat
   ```

   Или вручную:
   ```
   pyinstaller --noconfirm --name "Metalloemkost" --windowed --onefile ^
       --hidden-import "pandas" --hidden-import "openpyxl" --hidden-import "docx" ^
       --hidden-import "customtkinter" --hidden-import "PIL" ^
       --collect-all customtkinter --collect-all darkdetect main.py
   ```

3. Результат: `dist/Metalloemkost.exe`

---

## Сборка EXE без Windows (GitHub Actions)

Создайте репозиторий на GitHub и добавьте `.github/workflows/build.yml`:

```yaml
name: Build
on: [push]
jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt pyinstaller
      - run: pyinstaller --noconfirm --name Metalloemkost --windowed --onefile --hidden-import pandas --hidden-import openpyxl --hidden-import docx --hidden-import customtkinter --hidden-import PIL --collect-all customtkinter --collect-all darkdetect main.py
      - uses: actions/upload-artifact@v4
        with:
          name: Metalloemkost-Windows
          path: dist/Metalloemkost.exe
```

После push в репозиторий EXE появится в разделе Actions → Artifacts.
