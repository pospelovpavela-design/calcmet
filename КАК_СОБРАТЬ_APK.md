# Сборка Android APK

## Быстрый способ — GitHub Actions (бесплатно, 10 минут)

### Шаг 1: Создать репозиторий на GitHub
1. Зайти на github.com → New repository
2. Имя: `metalcalc` (или любое)
3. Нажать Create

### Шаг 2: Загрузить файлы
```bash
cd /Users/pospelovsfamily/Desktop/Металлоемкость
git init
git add main_android.py buildozer.spec requirements.txt \
        "Тип 1 здания с кранами" .github
git commit -m "Initial commit"
git remote add origin https://github.com/pospelovpavela-design/calcmet.git
git push -u origin main
```

### Шаг 3: Получить APK
- GitHub автоматически запустит сборку (Actions → Build Android APK)
- Через ~15 минут APK появится в разделе **Artifacts**
- Скачать и установить на телефон

---

## Альтернатива — Google Colab (без Git)

1. Открыть https://colab.research.google.com
2. Создать новый ноутбук, вставить:

```python
# Установка
!pip install buildozer cython

# Клонировать проект (или загрузить файлы через Files)
# ... загрузить main_android.py, buildozer.spec, данные ...

# Сборка
!buildozer -v android debug
```

3. В папке `bin/` появится `.apk`

---

## Структура файлов для сборки

```
проект/
├── main_android.py          ← Kivy-приложение
├── buildozer.spec           ← Конфиг сборки Android
├── Тип 1 здания с кранами/  ← Таблицы данных (xlsx, docx)
│   ├── металлоекмсоть покрытия.xlsx
│   ├── Металлоёмкость фахверк.xlsx
│   ├── Таблица металлоемкости на подкрановые конструкции.docx
│   └── Таблица металлоемкости на тормозные конструкции.docx
└── .github/
    └── workflows/
        └── build_apk.yml    ← CI/CD пайплайн
```
