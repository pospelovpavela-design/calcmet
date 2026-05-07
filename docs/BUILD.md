# Сборка релизов

## Android APK

### Автоматически через GitHub Actions (рекомендуется)

1. Сделать push в ветку `main`
2. Перейти: **Actions → Build Android APK**
3. Дождаться завершения (~15 мин)
4. Скачать APK из раздела **Artifacts**

### Вручную (Google Colab)

```python
!pip install buildozer cython
!buildozer -v android debug
# APK появится в папке bin/
```

---

## Windows EXE

### Автоматически через GitHub Actions

1. Push в `main` → **Actions → Build Windows EXE**
2. Скачать из **Artifacts**

### Вручную

```bash
pip install customtkinter pyinstaller
pyinstaller metal_windows.spec
# EXE в папке dist/
```

---

## macOS DMG

### Автоматически через GitHub Actions

1. Push в `main` → **Actions → Build macOS DMG**
2. Скачать из **Artifacts**

### Вручную

```bash
pip install customtkinter pyinstaller
pyinstaller metal_macos.spec
# DMG в папке dist/
```

---

## iOS / iPhone

### Локально через Xcode

```bash
./build_ios_local.sh
```

Скрипт создаёт `.venv-ios`, устанавливает `cython` и `kivy-ios`, собирает Kivy для `iphoneos-arm64` и `iphonesimulator-arm64`, создаёт Xcode-проект и открывает его.

Дальше в Xcode:

1. Подключить iPhone кабелем.
2. В Signing & Capabilities выбрать Team.
3. При необходимости задать уникальный Bundle Identifier.
4. Выбрать iPhone в списке устройств.
5. Нажать `Cmd+R`.

### Через GitHub Actions

Workflow `Build iOS (MetalCalc)` собирает приложение для iOS Simulator. Подписанный IPA для реального iPhone создаётся только при наличии Apple-секретов в репозитории.

---

## Структура spec-файлов

| Файл | Назначение |
|------|-----------|
| `buildozer.spec` | Android APK |
| `metal_windows.spec` | Windows EXE |
| `metal_macos.spec` | macOS DMG |
| `launcher_windows.spec` | Лаунчер Windows |
| `launcher_macos.spec` | Лаунчер macOS |
