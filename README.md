# CalcMet — Калькулятор металлоёмкости производственных зданий

Инструмент для расчёта металлоёмкости несущих конструкций производственных зданий по нормативным таблицам. Поддерживает многопролётные здания, крановые нагрузки, фахверк, кровельные конструкции.

## Платформы

| Платформа | Файл | Технология |
|-----------|------|-----------|
| Android   | `main.py` | Kivy / KivyMD |
| Windows / macOS | `main_desktop.py` | CustomTkinter |

## Что считает

- Стропильные и подстропильные фермы (уголки, двутавры, молодечненский прокат)
- Подкрановые балки и крановые рельсы
- Тормозные конструкции
- Фахверк (торцевой и продольный)
- Прогоны покрытия
- Многопролётные здания с суммированием

## Быстрый старт

### Desktop (Windows / macOS)

```bash
# 1. Клонировать
git clone https://github.com/pospelovpavela-design/calcmet.git
cd calcmet

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Запустить
python main_desktop.py
```

### Android

Собирается через GitHub Actions — см. [BUILD.md](docs/BUILD.md).

## Сборка релизов

| Артефакт | Workflow | Триггер |
|----------|----------|---------|
| Windows EXE | `build_exe.yml` | push в `main` |
| macOS DMG | `build_dmg.yml` | push в `main` |
| Android APK | `build_apk.yml` | push в `main` |

Собранные файлы доступны в разделе [Actions](../../actions) → выбрать workflow → Artifacts.

## Структура проекта

```
calcmet/
├── main.py                  # Android-версия (Kivy)
├── main_desktop.py          # Desktop-версия (CustomTkinter)
├── launcher.py              # Общий лаунчер
├── requirements.txt         # Python-зависимости
├── buildozer.spec           # Конфиг сборки Android
├── docs/
│   └── BUILD.md             # Инструкция по сборке APK/EXE/DMG
├── .github/
│   ├── workflows/           # CI/CD пайплайны
│   └── ISSUE_TEMPLATE/      # Шаблоны задач
└── Тип 1 здания с кранами/  # Нормативные таблицы (xlsx, docx)
```

## Вклад в проект

Читайте [CONTRIBUTING.md](CONTRIBUTING.md) — там описан процесс работы с ветками, оформление PR и code style.

## Лицензия

MIT
