# Файл восстановления контекста — MetalCalc

> Создан: 2026-03-14 · Обновлён 2026-05-07 после успешного запуска iOS-приложения на iPhone

---

## Состояние ветки

Ветка `main`. В этой сессии подготовлены и будут запушены правки для iPhone-сборки.

### Коммиты этой сессии (новейший первый)

| Хэш | Описание |
|---|---|
| `pending` | iOS: fix iPhone build/run setup and startup crash |
| `17b70f9` | docs: update verification plan — Block 3 formula analysis |
| `e11d888` | Tests: fix 5 failing + add etalon tests for blocks 1-4 |
| `07d267a` | Fix: calculation result not shown, save does nothing |
| `77eac55` | Add roof pie builder to iOS |
| `b42bf2d` | Fix AttributeError _btn_container |

---

## Что сделано в этой сессии

### 0. iOS/iPhone: приложение собрано и запустилось на iPhone (2026-05-07)

Подтверждено пользователем: приложение запустилось на iPhone после исправлений.

Сделанные правки:
- `main.py`: добавлен нижний safe-area для iPhone Home Indicator.
- `main.py`: исправлен startup crash `NameError: name 'cb' is not defined` в `_build_form()`.
- `build_ios_local.sh`: сборка переведена на локальный `.venv-ios`, автодоустановка `cython` и `kivy-ios`.
- `build_ios_local.sh`: сборка Kivy явно для `iphoneos-arm64` и `iphonesimulator-arm64`.
- `build_ios_local.sh`: добавлен патч установленного recipe `sdl2_mixer` для бага `NameError: join is not defined`.
- `build_ios_local.sh`: Xcode-проект настраивается как iPhone-only, deployment target 15.0, Bundle ID `ru.pospelov.metalcalc`.
- `build_ios_local.sh`: build phase `rsync` теперь исключает `.git/`, `.github/`, `.venv/`, `.venv-ios/`, `.pytest_cache/`, `__pycache__/`, `kivy-ios-build/` и использует `--delete-excluded`, чтобы не копировать сборочные артефакты внутрь `YourApp`.
- `.github/workflows/build_ios.yml`: синхронизирована iOS-сборка CI с локальными настройками.
- `.gitignore`: добавлены `.venv-ios/` и `kivy-ios-build/`.
- `README.md`, `docs/BUILD.md`: обновлены инструкции по iPhone/Xcode.

Важные ручные шаги в Xcode:
- Открывать проект: `kivy-ios-build/metalcalc-ios/metalcalc.xcodeproj`.
- `TARGETS -> metalcalc -> Signing & Capabilities -> Team`: выбрать Apple ID.
- Bundle Identifier: `ru.pospelov.metalcalc` или другой уникальный, если Xcode попросит.
- После правок build phase: `Product -> Clean Build Folder` (`Shift+Cmd+K`), затем `Cmd+R`.

Нерелевантные untracked файлы не трогать и не коммитить без отдельного запроса:
- `Проверка KNOWLEDGE_BASE_дополнена (1).docx`
- `методичка/`

### 1. Исправлен crash при запуске iOS (`b42bf2d`)
**Симптом:** `AttributeError: 'MetalApp' object has no attribute '_btn_container'`
**Причина:** `_add_span_block()` вызывается в `_build_form()` до инициализации `_btn_container`
**Исправление:** добавлен `if hasattr(self, '_btn_container'):` в `main.py`

### 2. Добавлен конструктор кровельного пирога (`77eac55`)
В `main.py` добавлены:
- `ROOF_MATERIALS` — 29 материалов с весом кН/м²
- `ROOF_PRESETS` — 4 пресета (Металл. профнастил, ж/б, утеплённая, мягкая)
- Методы: `_pie_update_total`, `_pie_add_layer`, `_pie_clear`, `_pie_apply_preset`
- UI: Spinner для выбора материала/пресета, BoxLayout со слоями, кнопки добавить/удалить/очистить
- `_read_params` читает `Q_roof` из суммы слоёв и передаёт `Q_roof_layers`
- `_format_results` выводит список слоёв пирога для каждого пролёта

### 3. Исправлено: расчёт не выводится и не сохраняется (`07d267a`)
**Причина:** traceback содержит `[` и `]` → Kivy markup parser падает внутри `except` → исключение
поглощается `Clock` → экран не переключается, `_last_result_text = ""`
**Исправление:**
- `tb_safe = tb.replace("[", "[[").replace("]", "]]")` перед вставкой в markup Label
- Обёртка screen-операций в `except` блоке в свой `try/except`
- `_last_result_text` устанавливается даже при ошибке
- Crash log пишется в `~/Documents/metalcalc_crash.log`
- `do_save_results` показывает сообщение если нет данных

### 4. Исправлены тесты + добавлены эталонные тесты (`e11d888`)
- Исправлены 5 тестов: коэффициенты режима приведены к текущей версии
- Добавлены 4 класса эталонных тестов:
  - `TestEtalonBlok1Purlins` — прогоны (qp=0.535 → Швеллер 22)
  - `TestEtalonBlok2Trusses` — фермы (Уголки, 24м, 4.0 кН/м² → 4.29 кг/м²)
  - `TestEtalonBlok3CraneBeamM1` — подкрановые балки М1 (100т, проверка коэффициентов)
  - `TestEtalonBlok4CraneBeamM2` — подкрановые балки М2 (20т → 150 кг/м)
- **Итог: 226 passed, 0 failed**

### 5. Обновлён VERIFICATION_PLAN.md (`17b70f9`)
- Добавлен анализ расхождения формулы Блока 3
- Обновлены открытые вопросы
- Заголовок: "226 PASSED, 0 FAILED"

---

## Открытые вопросы

### ✅ Вопрос 1 (ЗАКРЫТ): Формула подкрановых балок М1

**Сверено с методикой ЦНИИ** (разд. «Подкрановые балки»):
- Формула: `Gпб,n = (αпб × Lпб + qр) × Lпб × kпб` — код ей соответствует.
- `CRANE_Q_EQUIV` в расчёте балок не нужен — он только для `Dmax` колонны.
- Исправлено: `kпб` 1.4 → **1.2**; таблица `CRANE_BEAM_ALPHA` пересчитана по диапазонам методики.
- Эталон: Q=100т, 6м, 7-8К → **45.91 т** (тест обновлён).

### ❗ Вопрос 2: Обоснование коэф. 7-8К = 1.80
- Источник не указан — нужна ссылка на методику.

### ❗ Вопрос 3: Откуда CRANE_Q_EQUIV ×2.5?
- Используется только в колоннах для Dmax; сейчас это рабочая калибровка, первоисточник отдельно не найден.

### Вопрос 4: Проверить FAKHVERK_DATA против таблиц методики
### Вопрос 5: Проверить SUBTRUSS_MASSES против таблиц методики
### Вопрос 6: Пример расчёта колонны с реальными данными (~8т на колонну)

---

## Что нужно сделать следующим

1. **iOS**: запуск на iPhone подтверждён. При следующих изменениях пересобрать Xcode проект: `Shift+Cmd+K` → `Cmd+R`.

2. **Блок 3 закрыт** — αпб и kпб=1.2 исправлены по методике, тесты проходят.

3. **Блоки 5-9**: продолжить по `VERIFICATION_PLAN.md` (связи, колонны, фахверк, подстропильные, опоры)

4. **Вопрос 2**: найти обоснование коэф. 7-8К = 1.80 в методике.

5. **Вопрос 3**: при появлении первоисточника сверить CRANE_Q_EQUIV и заменить рабочую калибровку.

---

## Ключевые файлы

| Файл | Назначение |
|---|---|
| `main.py` | iOS/Kivy версия — основные правки этой сессии |
| `main_desktop.py` | Desktop/CustomTkinter — логика расчёта |
| `tests/test_main_desktop.py` | 226 тестов, все проходят |
| `VERIFICATION_PLAN.md` | Подробный план проверки с анализом формул |
| `KNOWLEDGE_BASE.md` | Документация формул и констант |
| `CONTEXT_RECOVERY.md` | Этот файл |

---

## Технические заметки

- **Kivy markup**: любые `[` и `]` в динамическом тексте нужно экранировать как `[[` и `]]`
- **Kivy BoxLayout dynamic height**: `size_hint_y=None` + `bind(minimum_height=setter('height'))`
- **Ry стали С245**: 240 000 кН/м² (24 кН/см²) — критическая константа, ранее была 24 000 → масса колонн ×10
- **iOS export**: `~/Documents/MetalCalc_YYYYMMDD_HHmmss.txt`
- **iOS crash log**: `~/Documents/metalcalc_crash.log`
