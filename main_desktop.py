#!/usr/bin/env python3
"""
Расчетный модуль металлоемкости производственных зданий с мостовыми кранами.
Метод 1 — эмпирические формулы (hardcoded).
Метод 2 — чтение таблиц из xlsx/docx.
"""

import os
import sys
import math
import traceback
import customtkinter as ctk
from tkinter import messagebox, scrolledtext
import tkinter as tk
import pandas as pd
from docx import Document

# ─────────────────────────────────────────────────────────
#  ПУТИ К ДАННЫМ  (работает и как скрипт, и в PyInstaller-бандле)
# ─────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    # Запущен как .app / .exe (PyInstaller)
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR  = os.path.join(BASE_DIR, "Тип 1 здания с кранами")

POKRYTIE_XLSX  = os.path.join(DATA_DIR, "металлоекмсоть покрытия.xlsx")
FAKHVERK_XLSX  = os.path.join(DATA_DIR, "Металлоёмкость фахверк.xlsx")
CRANE_BEAMS_DOCX = os.path.join(DATA_DIR, "Таблица металлоемкости на подкрановые конструкции.docx")
BRAKE_DOCX       = os.path.join(DATA_DIR, "Таблица металлоемкости на тормозные конструкции.docx")

# ─────────────────────────────────────────────────────────
#  HARDCODED ДАННЫЕ (Метод 1)
# ─────────────────────────────────────────────────────────

# Прогоны — Таблица 3: (нагрузка т/м, масса 6м кг, масса 12м кг, имя профиля)
PURLIN_TABLE = [
    (0.45, 110.4,  220.8, "Швеллер 20"),
    (0.65, 126.0,  252.0, "Швеллер 22"),
    (0.90, 144.0,  288.0, "Швеллер 24"),
    (1.25, 166.2,  332.4, "Швеллер 27"),
    (1.70, 190.8,  381.6, "Швеллер 30"),
    (2.50, 220.8,  441.6, "2×Швеллер 20"),
]

# Коэффициент αпф для подстропильных ферм
# αпф = (R - 100)*0.0002 + 0.044, R кН (диапазон 100-400 кН)
# Lпф = 12 м (шаг колонн)

# Коэффициент αпб для подкрановых балок по г/п крана (кН/м на м)
CRANE_BEAM_ALPHA = {
    5:   0.08,
    10:  0.09,
    20:  0.12,
    32:  0.15,
    50:  0.18,
    80:  0.22,
    100: 0.26,
    125: 0.30,
    200: 0.36,
    320: 0.40,
    400: 0.45,
}

# Вес рельса qр (кН/м) по г/п крана
RAIL_WEIGHT_KN = {
    5:   0.461,   # КР-70
    10:  0.461,
    20:  0.461,
    32:  0.598,   # КР-80
    50:  0.598,
    80:  0.831,   # КР-100
    100: 1.135,   # КР-120
    125: 1.135,
    200: 1.135,
    320: 1.417,   # КР-140
    400: 1.417,
}

# Высота балки (отн. Lпб) для расчёта Н-верх: (г/п: hб/Lпб при шаге 6м, при 12м)
BEAM_HEIGHT_RATIO = {
    20:  (1/7,  1/9),
    32:  (1/7,  1/9),
    50:  (1/6,  1/8.5),
    80:  (1/6,  1/7.5),
    100: (1/6,  1/7),
    125: (1/6,  1/7),
    160: (1/6,  1/7),
    200: (1/6,  1/7),
}

# Нормативные эквивалентные нагрузки q (кН/м) — Таблица 6.2 в методике
# Значения по г/п крана (типовые для режима 5К, ГОСТ 1575)
CRANE_Q_EQUIV = {
    5:   8,
    10:  12,
    20:  20,
    32:  28,
    50:  38,
    80:  55,
    100: 68,
    125: 80,
    200: 105,
    320: 145,
    400: 175,
}

# Связи покрытия — кг/м2 (из покрытие.xlsx, горизонтальные связи)
BRACING_COVERAGE = {
    # (г/п крана <= 120т, шаг ферм 6м): 15 кг/м2
    # (г/п крана <= 120т, шаг ферм 12м): 35 кг/м2
    # (г/п крана <= 400т, шаг ферм 6м): 40 кг/м2
    # (г/п крана <= 400т, шаг ферм 12м): 55 кг/м2
}

# ─────────────────────────────────────────────────────────
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ─────────────────────────────────────────────────────────

def closest_alpha_pb(q_kn: float) -> float:
    """Вернуть αпб для г/п крана (кН)."""
    caps = sorted(CRANE_BEAM_ALPHA.keys())
    for cap in caps:
        if q_kn <= cap:
            return CRANE_BEAM_ALPHA[cap]
    return CRANE_BEAM_ALPHA[caps[-1]]


def rail_weight(q_kn: float) -> float:
    """Вес рельса qр (кН/м) для г/п крана (кН)."""
    caps = sorted(RAIL_WEIGHT_KN.keys())
    for cap in caps:
        if q_kn <= cap:
            return RAIL_WEIGHT_KN[cap]
    return RAIL_WEIGHT_KN[caps[-1]]


def q_equiv(q_kn: float) -> float:
    """Нормативная эквивалентная нагрузка q (кН/м) для г/п крана."""
    caps = sorted(CRANE_Q_EQUIV.keys())
    for cap in caps:
        if q_kn <= cap:
            return CRANE_Q_EQUIV[cap]
    return CRANE_Q_EQUIV[caps[-1]]


def select_purlin(load_tm: float, span_m: float):
    """
    Подобрать прогон по расчётной нагрузке (т/м) и пролёту (6 или 12 м).
    Возвращает (масса кг, имя профиля).
    """
    for max_load, mass_6, mass_12, name in PURLIN_TABLE:
        if load_tm <= max_load:
            mass = mass_6 if span_m <= 6 else mass_12
            return mass, name
    # Если нагрузка превысила таблицу — взять наибольший
    _, mass_6, mass_12, name = PURLIN_TABLE[-1]
    mass = mass_6 if span_m <= 6 else mass_12
    return mass, f"{name} (нагрузка превышает таблицу!)"


def interp_table(loads, masses, target):
    """Линейная интерполяция/ближайшее большее в таблице."""
    for i, ld in enumerate(loads):
        if target <= ld:
            return masses[i]
    return masses[-1]


def ceil_to_table(target, values):
    """Округлить до ближайшего большего значения из списка."""
    for v in sorted(values):
        if target <= v:
            return v
    return sorted(values)[-1]


# ─────────────────────────────────────────────────────────
#  ФУНКЦИИ ЧТЕНИЯ ТАБЛИЦ (Метод 2)
# ─────────────────────────────────────────────────────────

def read_pokrytie() -> pd.DataFrame:
    return pd.read_excel(POKRYTIE_XLSX, header=None, sheet_name=0)


def read_fakhverk() -> pd.DataFrame:
    return pd.read_excel(FAKHVERK_XLSX, header=None, sheet_name="Расчеты")


def get_truss_mass_m2(
    df_cov: pd.DataFrame,
    truss_type: str,  # "Уголки", "Двутавры", "Молодечно"
    span_m: float,    # пролёт здания (L)
    load_tm: float,   # нагрузка т/м.п. на ферму
) -> tuple:
    """
    Вернуть (масса 1 фермы т, имя секции).
    Поиск по таблице покрытие.xlsx.
    """
    type_map = {
        "Уголки":   "Фермы из уголков",
        "Двутавры": "Фермы из двутавров",
        "Молодечно": "Фермы молодечно",
    }
    section_label = type_map.get(truss_type, "Фермы из уголков")
    span_label = f"Пролет {int(span_m)}м"

    # Найти строку-заголовок секции
    section_row = None
    for i, row in df_cov.iterrows():
        if str(row[0]).strip() == section_label:
            section_row = i
            break
    if section_row is None:
        return None, f"Секция '{section_label}' не найдена"

    # Найти строку пролёта внутри секции
    span_row = None
    for i in range(section_row, min(section_row + 10, len(df_cov))):
        if str(df_cov.iloc[i, 0]).strip() == span_label:
            span_row = i
            break
    if span_row is None:
        return None, f"Пролёт '{span_label}' не найден в секции"

    loads_row  = df_cov.iloc[span_row + 1]
    masses_row = df_cov.iloc[span_row + 2]

    loads  = []
    masses = []
    for col in range(1, len(loads_row)):
        try:
            ld = float(loads_row[col])
            ms = float(masses_row[col])
            loads.append(ld)
            masses.append(ms)
        except (ValueError, TypeError):
            pass

    if not loads:
        return None, "Данные нагрузок не найдены"

    mass = interp_table(loads, masses, load_tm)
    return mass, f"{section_label} пролёт {int(span_m)}м"


def get_subtruss_mass_m2(df_cov: pd.DataFrame, R_t: float) -> float:
    """
    Масса 1 подстропильной фермы по нагрузке R (тонн).
    Из таблицы покрытие.xlsx.
    """
    sub_row = None
    for i, row in df_cov.iterrows():
        if str(row[0]).strip() == "Подстропильные фермы":
            sub_row = i
            break
    if sub_row is None:
        return None

    loads_row  = df_cov.iloc[sub_row + 1]
    masses_row = df_cov.iloc[sub_row + 2]

    loads  = []
    masses = []
    for col in range(1, len(loads_row)):
        try:
            ld = float(loads_row[col])
            ms = float(masses_row[col])
            loads.append(ld)
            masses.append(ms)
        except (ValueError, TypeError):
            pass

    if not loads:
        return None

    # Округлить R до ближайшего большего
    R_ceil = ceil_to_table(R_t, loads)
    return interp_table(loads, masses, R_ceil)


def get_bracing_kgm2(q_crane_t: float, step_farm_m: float) -> float:
    """Расход стали на связи покрытия (кг/м2) из таблицы."""
    if q_crane_t <= 120:
        return 15.0 if step_farm_m <= 6 else 35.0
    else:
        return 40.0 if step_farm_m <= 6 else 55.0


def _parse_docx_table_simple(doc_path: str, table_idx: int) -> list:
    """Вернуть список списков строк ячеек docx-таблицы (уникальные по строке)."""
    doc = Document(doc_path)
    table = doc.tables[table_idx]
    result = []
    for row in table.rows:
        seen = set()
        cells = []
        for cell in row.cells:
            txt = cell.text.strip().replace('\n', ' ')
            if txt not in seen:
                cells.append(txt)
                seen.add(txt)
        if any(c.strip() for c in cells):
            result.append(cells)
    return result


def get_crane_beam_kgm_m2(
    q_crane_t: float,   # г/п крана, т
    span_pb_m: float,   # пролёт п/б = шаг колонн, м
    n_cranes: int,      # количество кранов
) -> float:
    """
    Металлоемкость подкрановой балки (кг/м) из таблицы docx.
    Возвращает кг/м или None.
    """
    try:
        # Таблица 1: Q=5-50т
        if q_crane_t <= 50:
            rows = _parse_docx_table_simple(CRANE_BEAMS_DOCX, 0)
            # Ищем строку с нужным пролётом
            span_str = f"{int(span_pb_m)} м"
            for row in rows:
                if row and span_str in row[0]:
                    # Определить индекс столбца по г/п и кол-ву кранов
                    # Структура: пролет | данные по Q=5,10,20,32,50 и режимам
                    # Упрощение: берём данные по позиции
                    vals = []
                    for c in row[1:]:
                        try:
                            vals.append(float(c))
                        except (ValueError, TypeError):
                            pass
                    if not vals:
                        return None
                    # Карта: (Q_t, n_cranes) → индекс (приблизительный)
                    # Таблица 1 строка 6м: [5т_1к, 5т_2к, ...10т..., ...50т...]
                    # Используем позицию: каждые 2 значения на г/п
                    q_order = [5, 10, 20, 32, 50]
                    try:
                        q_idx = min(range(len(q_order)),
                                    key=lambda i: abs(q_order[i] - q_crane_t))
                        crane_idx = q_idx * 2 + (0 if n_cranes == 1 else 1)
                        if crane_idx < len(vals):
                            return vals[crane_idx]
                    except Exception:
                        return vals[0]
        # Таблица 2: Q=80-400т
        else:
            rows = _parse_docx_table_simple(CRANE_BEAMS_DOCX, 1)
            span_str = str(int(span_pb_m))
            for row in rows:
                if row and row[0].startswith(span_str):
                    vals = []
                    for c in row[1:]:
                        try:
                            vals.append(float(c))
                        except (ValueError, TypeError):
                            pass
                    if not vals:
                        return None
                    q_order = [80, 100, 125, 200, 400]
                    try:
                        q_idx = min(range(len(q_order)),
                                    key=lambda i: abs(q_order[i] - q_crane_t))
                        crane_idx = q_idx * 2 + (0 if n_cranes == 1 else 1)
                        if crane_idx < len(vals):
                            return vals[crane_idx]
                    except Exception:
                        return vals[0]
    except Exception as e:
        print(f"Ошибка чтения подкрановой балки: {e}")
    return None


def get_brake_kgm(
    q_crane_t: float,
    span_pb_m: float,
    n_cranes: int,
    with_passage: bool,   # True = С проходом, False = Без прохода
    is_edge: bool,        # True = крайний ряд
) -> float:
    """
    Металлоемкость тормозных конструкций (кг/м) из таблицы docx.
    """
    try:
        table_idx = 0 if q_crane_t <= 50 else 1
        rows = _parse_docx_table_simple(BRAKE_DOCX, table_idx)

        span_str = f"{int(span_pb_m)} м"
        row_type  = "Крайний" if is_edge else "Средний"
        pass_type = "С проходом" if with_passage else "Без прохода"

        for row in rows:
            row_full = " ".join(row)
            if (span_str in row[0] if row else False) \
               and row_type in row_full and pass_type in row_full:
                vals = []
                for c in row:
                    try:
                        v = float(c)
                        vals.append(v)
                    except (ValueError, TypeError):
                        pass
                if vals:
                    idx = 0 if n_cranes == 1 else min(1, len(vals) - 1)
                    return vals[idx]
    except Exception as e:
        print(f"Ошибка чтения тормозных конструкций: {e}")
    return None


def get_fakhverk_kgm2(
    df_fakh: pd.DataFrame,
    step_col_m: float,      # шаг колонн
    has_fakhverk_post: bool, # наличие стойки фахверка
    h_building: float,       # высота здания, м
    rig_load: float,         # нагрузка на ригели фахверка, кг/м.п.
) -> float:
    """
    Расход стали на фахверк (кг/м2 площади стен) из таблицы.
    """
    try:
        # Определить тип схемы
        if step_col_m <= 6 and has_fakhverk_post:
            type_row = 7   # Row 7 = III тип: шаг 6м со стойками фахверка
        elif step_col_m <= 6:
            type_row = 5   # Row 5 = I тип: шаг 6м
        else:
            type_row = 6   # Row 6 = II тип: шаг 12м

        # Определить столбец нагрузки
        if rig_load <= 0:
            load_col_start = 2   # Без нагрузки
        elif rig_load <= 100:
            load_col_start = 5   # 100 кг/м.п.
        else:
            load_col_start = 8   # 300 кг/м.п.

        # Определить высоту (столбец): до 10, до 20, до 40
        if h_building <= 10:
            h_offset = 0
        elif h_building <= 20:
            h_offset = 1
        else:
            h_offset = 2

        col = load_col_start + h_offset
        row = df_fakh.iloc[type_row]
        val = float(row.iloc[col])
        return val
    except Exception as e:
        print(f"Ошибка чтения фахверк: {e}")
        return None


def get_pipe_support_kgm2(df_fakh: pd.DataFrame, building_type: str) -> float:
    """
    Расход стали на опоры трубопроводов (кг/м2 площади здания) из таблицы.
    """
    try:
        # Row 13: Основные 11-22, Энергоносители 23-40, Вспомогательные 2-4
        type_map = {
            "Основные производственные": (11, 22),
            "Здания энергоносителей":    (23, 40),
            "Вспомогательные здания":    (2, 4),
        }
        rng = type_map.get(building_type, (11, 22))
        return (rng[0] + rng[1]) / 2  # среднее, т.к. таблица даёт диапазон
    except Exception:
        return None


# ─────────────────────────────────────────────────────────
#  ОСНОВНАЯ ЛОГИКА РАСЧЁТА
# ─────────────────────────────────────────────────────────

def calculate(params: dict) -> dict:
    """
    Выполнить расчёт металлоемкости.
    params — словарь входных параметров.
    Возвращает словарь результатов.
    """
    res = {}
    log = []

    # ── Входные параметры ──────────────────────────────────
    L_build   = params["L_build"]    # длина здания по осям, м
    W_build   = params["W_build"]    # ширина здания, м
    L_span    = params["L_span"]     # пролёт фермы, м
    B_step    = params["B_step"]     # шаг ферм, м (пролёт прогона)
    col_step  = params["col_step"]   # шаг колонн, м (6 или 12)
    h_rail    = params["h_rail"]     # уровень головки рельса, м
    Q_snow    = params["Q_snow"]     # снеговая нагрузка, кН/м2
    Q_dust    = params["Q_dust"]     # пыль, кН/м2
    Q_roof    = params["Q_roof"]     # кровля, кН/м2
    Q_purlin  = params["Q_purlin"]   # вес прогона, кН/м2
    yc        = params["yc"]         # коэф. уровня ответственности
    truss_type = params["truss_type"]  # "Уголки"/"Двутавры"/"Молодечно"
    q_crane_t = params["q_crane_t"]  # г/п крана, т
    n_cranes  = params["n_cranes"]   # кол-во кранов (1 или 2)
    with_pass = params["with_pass"]  # тормозные пути: True=с проходом
    rig_load  = params["rig_load"]   # нагрузка на ригели фахверка, кг/м.п.
    has_post  = params["has_post"]   # стойка фахверка (bool)
    bld_type  = params["bld_type"]   # тип здания для опор трубопроводов

    # Проверить наличие файлов
    missing = []
    for path in [POKRYTIE_XLSX, FAKHVERK_XLSX, CRANE_BEAMS_DOCX, BRAKE_DOCX]:
        if not os.path.exists(path):
            missing.append(os.path.basename(path))
    if missing:
        raise FileNotFoundError(
            "Не найдены файлы с таблицами:\n" + "\n".join(missing)
        )

    # Загрузить таблицы
    df_cov  = read_pokrytie()
    df_fakh = read_fakhverk()

    # ── Геометрия ─────────────────────────────────────────
    H_lower  = h_rail          # высота подкрановой части, м

    # Площадь здания
    S_floor = L_build * W_build
    # Периметр стен (предварительно для прогонов; H_full уточняется в разделе колонн)
    P_walls = 2 * (L_build + W_build)
    # Предварительная высота для стен (уточняется после расчёта колонн)
    H_full_est = h_rail + 1.5
    S_walls_est = P_walls * H_full_est

    log.append(f"Площадь пола: {S_floor:.1f} м²")

    # ── 1. ПРОГОНЫ (Метод 1) ──────────────────────────────
    step_purlin = 3.0  # шаг прогонов, м (принято)
    # Расчётная нагрузка на 1 прогон (кН/м)
    q_pr_knm = (Q_roof + Q_purlin + Q_snow + Q_dust) * step_purlin * yc
    q_pr_tm  = q_pr_knm / 9.81  # т/м

    mass_purlin, purlin_name = select_purlin(q_pr_tm, B_step)
    # Количество прогонов в 1 шаге ферм
    n_pr = L_span / step_purlin + 3
    # Расход на 1 м2 покрытия
    g_purlin_kgm2 = mass_purlin * n_pr / (L_span * B_step)
    G_purlin_total = g_purlin_kgm2 * S_floor

    res["прогоны"] = {
        "метод": "1",
        "профиль": purlin_name,
        "нагрузка_тм": round(q_pr_tm, 3),
        "масса_1шт_кг": round(mass_purlin, 1),
        "n_в_шаге": round(n_pr, 1),
        "расход_кгм2": round(g_purlin_kgm2, 2),
        "масса_общая_т": round(G_purlin_total / 1000, 2),
    }
    log.append(f"Прогоны: q={q_pr_tm:.3f} т/м → {purlin_name}, "
               f"g={g_purlin_kgm2:.2f} кг/м²")

    # ── 2. СТРОПИЛЬНЫЕ ФЕРМЫ ─────────────────────────────
    # Суммарная нормативная нагрузка gn (кН/м2)
    # Вес связей принимается 0.05 кН/м2 предварительно
    g_links_est = 0.05  # кН/м2 (связи, предварительно)
    gn_total = Q_snow + Q_dust + Q_roof + Q_purlin + g_links_est

    # Нагрузка на 1 м.п. фермы (т/м)
    Q_total_knm = (gn_total) * B_step * yc
    Q_total_tm  = Q_total_knm / 9.81

    g_truss_m1 = None
    g_truss_m2 = None

    # Метод 1 — только для уголков
    if truss_type == "Уголки":
        alpha_f = 1.4  # С235-С285
        gamma_n = yc
        # Gф,n (кН) = (gn*bф/1000 + 0.018)*αф*L²/0.85 * γn
        # gn — в кН/м2, bф в м → результат в кН
        G_truss_m1_kn = (gn_total * B_step / 1000 + 0.018) * alpha_f * L_span**2 / 0.85 * gamma_n
        G_truss_m1_t = G_truss_m1_kn / 9.81  # кН → тонны
        n_trusses = (L_build / B_step + 1)
        g_truss_m1 = G_truss_m1_t * 1000 * n_trusses / S_floor  # кг/м2
        log.append(f"Ферма М1: Gф={G_truss_m1_t*1000:.0f} кг, "
                   f"g={g_truss_m1:.2f} кг/м²")

    # Метод 2 — из таблицы
    mass_truss_t, truss_label = get_truss_mass_m2(
        df_cov, truss_type, L_span, Q_total_tm
    )
    if mass_truss_t is not None:
        n_trusses = (L_build / B_step + 1)
        g_truss_m2 = mass_truss_t * 1000 * n_trusses / S_floor  # кг/м2
        log.append(f"Ферма М2: 1 ферма={mass_truss_t*1000:.0f} кг "
                   f"(нагрузка {Q_total_tm:.2f} т/м), g={g_truss_m2:.2f} кг/м²")
    else:
        log.append(f"Ферма М2: {truss_label}")

    # Вес фермы для дальнейших расчётов (используем М2 если есть, иначе М1)
    G_truss_1_kg = (mass_truss_t * 1000) if mass_truss_t else (
        G_truss_m1_t * 1000 if truss_type == "Уголки" else None
    )

    res["фермы"] = {
        "нагрузка_тм": round(Q_total_tm, 3),
        "М1_расход_кгм2": round(g_truss_m1, 2) if g_truss_m1 else "н/п",
        "М2_расход_кгм2": round(g_truss_m2, 2) if g_truss_m2 else "н/п",
        "масса_1_фермы_кг": round(G_truss_1_kg, 1) if G_truss_1_kg else "н/п",
        "масса_общая_т_М1": round(g_truss_m1 * S_floor / 1000, 2) if g_truss_m1 else "н/п",
        "масса_общая_т_М2": round(g_truss_m2 * S_floor / 1000, 2) if g_truss_m2 else "н/п",
    }

    # ── 3. СВЯЗИ ПОКРЫТИЯ (Метод 2) ───────────────────────
    g_bracing = get_bracing_kgm2(q_crane_t, B_step)
    G_bracing_total = g_bracing * S_floor
    res["связи_покрытия"] = {
        "метод": "2",
        "расход_кгм2": g_bracing,
        "масса_общая_т": round(G_bracing_total / 1000, 2),
    }
    log.append(f"Связи покрытия: {g_bracing:.0f} кг/м²")

    # ── 4. ПОДСТРОПИЛЬНЫЕ ФЕРМЫ ───────────────────────────
    G_sub_m1 = None
    G_sub_m2 = None
    g_sub_m1 = None
    g_sub_m2 = None

    if col_step == 12 and B_step < col_step:
        # Реакция стропильной фермы (М1): R = Qобщ * L / 2
        R_kn = Q_total_knm * L_span / 2  # кН
        R_t  = R_kn / 9.81

        # Метод 1
        R_for_alpha = max(100, min(R_kn, 400))
        alpha_pf = (R_for_alpha - 100) * 0.0002 + 0.044
        Lpf = 12.0  # м (пролёт п/ф = шаг колонн)
        G_sub_m1_t = alpha_pf * Lpf**2  # т
        n_sub = (L_build / col_step) * (W_build / L_span - 1) if W_build > L_span else 0
        if n_sub <= 0:
            n_sub = L_build / col_step
        g_sub_m1 = G_sub_m1_t * 1000 * n_sub / S_floor  # кг/м2

        # Метод 2
        mass_sub_t = get_subtruss_mass_m2(df_cov, R_t)
        if mass_sub_t is not None:
            g_sub_m2 = mass_sub_t * 1000 * n_sub / S_floor  # кг/м2

        log.append(f"Подстроп. фермы: R={R_kn:.0f} кН ({R_t:.1f} т), "
                   f"αпф={alpha_pf:.4f}, Gпф={G_sub_m1_t*1000:.0f} кг (М1)")

        res["подстропильные_фермы"] = {
            "R_кн": round(R_kn, 1),
            "R_т": round(R_t, 2),
            "alpha_pf": round(alpha_pf, 4),
            "М1_расход_кгм2": round(g_sub_m1, 2) if g_sub_m1 else "н/п",
            "М2_расход_кгм2": round(g_sub_m2, 2) if g_sub_m2 else "н/п",
            "масса_общая_т_М1": round(g_sub_m1 * S_floor / 1000, 2) if g_sub_m1 else "н/п",
            "масса_общая_т_М2": round(g_sub_m2 * S_floor / 1000, 2) if g_sub_m2 else "н/п",
        }
    else:
        res["подстропильные_фермы"] = {"примечание": "Не требуются (шаг колонн = шагу ферм)"}

    # ── 5. ПОДКРАНОВЫЕ БАЛКИ ─────────────────────────────
    # Метод 1
    alpha_pb = closest_alpha_pb(q_crane_t)
    qr       = rail_weight(q_crane_t)
    k_pb     = 1.4
    L_pb     = float(col_step)  # пролёт п/б = шаг колонн

    # G п/б (нормативная масса балки + рельс + тормоза) в кН
    G_pb_kn  = (alpha_pb * L_pb + qr) * L_pb * k_pb
    G_pb_kg  = G_pb_kn / 9.81 * 1000  # неверная формула в методике — G уже в кН*?

    # Методика: Gпб,n = (αпб * Lпб + qр) * Lпб * kпб — результат в кН (т.к. α в кН/м²)
    # Переводим в кг:
    G_pb_kg  = G_pb_kn * 100  # α в кН/м/м, Lпб в м → кН/м → * Lпб → кН → *100≈кг
    # Аппроксимируем: (α_кН/м * L + qр_кН/м) * L * kпб = кН — это уже масса?
    # Используем более практичный подход:
    # Gпб = (α * L + q_rail) * L * k (т) — α в т/м/м
    alpha_pb_t = alpha_pb / 9.81  # перевод: если α был в кН/м/м → т/м/м
    G_pb_t = (alpha_pb_t * L_pb + qr / 9.81) * L_pb * k_pb

    # Расход на 1 м2 здания (с учётом крайних + средних рядов)
    n_bays_along = math.ceil(L_build / col_step)
    # Крайние ряды — по 2 ряда (А и В), средние — при многопролётности
    n_rows_edge = 2
    n_rows_mid  = max(0, round(W_build / L_span) - 1)
    n_pb_total  = (n_rows_edge + n_rows_mid * 2) * n_bays_along

    G_pb_total_m1_t = G_pb_t * n_pb_total
    g_pb_m1 = G_pb_total_m1_t * 1000 / S_floor  # кг/м2

    # Метод 2 — из таблицы
    # Крайний ряд
    pb_edge_kgm = get_crane_beam_kgm_m2(q_crane_t, L_pb, n_cranes)
    br_edge_kgm = get_brake_kgm(q_crane_t, L_pb, n_cranes, with_pass, is_edge=True)
    # Средний ряд
    pb_mid_kgm  = get_crane_beam_kgm_m2(q_crane_t, L_pb, n_cranes)
    br_mid_kgm  = get_brake_kgm(q_crane_t, L_pb, n_cranes, with_pass, is_edge=False)

    if pb_edge_kgm and br_edge_kgm is not None:
        total_edge_kgm = pb_edge_kgm + (br_edge_kgm or 0)
        total_mid_kgm  = (pb_mid_kgm or 0) + (br_mid_kgm or 0)
        G_pb_edge_t = total_edge_kgm * L_pb * n_bays_along * n_rows_edge / 1000
        G_pb_mid_t  = total_mid_kgm  * L_pb * n_bays_along * n_rows_mid  / 1000
        G_pb_total_m2_t = G_pb_edge_t + G_pb_mid_t
        g_pb_m2 = G_pb_total_m2_t * 1000 / S_floor
    else:
        G_pb_total_m2_t = None
        g_pb_m2 = None

    log.append(f"Подкрановые балки М1: α={alpha_pb}, G={G_pb_t:.2f} т, "
               f"g={g_pb_m1:.2f} кг/м²")

    res["подкрановые_балки"] = {
        "alpha_pb": alpha_pb,
        "q_rail_кнм": round(qr, 3),
        "L_pb_м": L_pb,
        "G_1пб_t_М1": round(G_pb_t, 2),
        "кг/м_крайн": pb_edge_kgm,
        "кг/м_сред":  pb_mid_kgm,
        "тормоз_кгм_крайн": br_edge_kgm,
        "тормоз_кгм_сред":  br_mid_kgm,
        "М1_расход_кгм2": round(g_pb_m1, 2),
        "М2_расход_кгм2": round(g_pb_m2, 2) if g_pb_m2 else "н/п",
        "масса_общая_т_М1": round(G_pb_total_m1_t, 2),
        "масса_общая_т_М2": round(G_pb_total_m2_t, 2) if G_pb_total_m2_t else "н/п",
    }

    # ── 6. КОЛОННЫ (Метод 1) ──────────────────────────────
    # Параметры колонны
    rho   = 78.5   # кН/м³
    Ry    = 24.0   # кН/см²  → 24000 кН/м²
    psi_upper = 1.4   # ψк для сплошной надкрановой части
    psi_lower = 2.1   # ψк для сквозной подкрановой части
    kM_upper  = 0.275 # кМ для надкрановой части
    kM_lower  = 0.45  # кМ для подкрановой части

    # Высоты частей колонны
    # H_upper — надкрановая: от верха подкрановой балки до низа фермы
    hb_ratio = BEAM_HEIGHT_RATIO.get(
        min(BEAM_HEIGHT_RATIO.keys(), key=lambda k: abs(k - q_crane_t)),
        (1/7, 1/9)
    )
    h_pb = col_step * (hb_ratio[0] if col_step <= 6 else hb_ratio[1])
    h_rail_h = 0.12  # высота рельса, м (КР-70 типично)
    H_upper = max(1.5, h_pb + h_rail_h + 0.3)  # мин 1.5м
    H_lower = h_rail  # высота подкрановой части = уровень головки рельса

    H_full  = H_upper + H_lower
    S_walls = P_walls * H_full

    log.append(f"Высота здания (ориент.): {H_full:.1f} м (надкр.={H_upper:.1f}, подкр.={H_lower:.1f})")
    log.append(f"Площадь стен: {S_walls:.1f} м²")

    # Стеновая нагрузка на колонну (сэндвич-панель gст ≈ 0.25 кН/м²)
    gst = 0.25  # кН/м2 стены
    alpha_win = 0.15  # коэф. проёмов
    G_wall_upper_kn = gst * H_upper * (1 - alpha_win) * col_step
    G_wall_lower_kn = gst * H_lower * (1 - alpha_win) * col_step

    # ΣFв (кН) — нагрузка в верхней части колонны (крайний ряд А)
    ΣFv_kn = (Q_roof + Q_purlin + Q_snow + Q_dust) * col_step * L_span / 2 + G_wall_upper_kn

    # Масса надкрановой части (кН — вес)
    G_col_upper_kn = ΣFv_kn * rho * psi_upper * H_upper / (kM_upper * 24000)

    # Вертикальное давление крана: Dmax = q * B * k1 * γc (k2=1, разрезные балки)
    k1   = 1.1
    q_eq = q_equiv(q_crane_t)
    D_max_kn = q_eq * col_step * k1 * yc

    # ΣFн (кН) — нагрузка в нижней части колонны
    # G_pb_kn — уже в кН (сила веса балки), добавляем напрямую
    ΣFn_kn = ΣFv_kn + D_max_kn + G_pb_kn + G_wall_lower_kn + G_col_upper_kn

    # Масса подкрановой части (кН — вес)
    G_col_lower_kn = ΣFn_kn * rho * psi_lower * H_lower / (kM_lower * 24000)

    G_col_total_kn = G_col_upper_kn + G_col_lower_kn
    G_col_total_kg = G_col_total_kn / 9.81 * 1000

    # Число колонн
    n_col_along = round(L_build / col_step) + 1
    n_rows = round(W_build / L_span) + 1
    n_col_total = n_col_along * n_rows

    G_col_all_t = G_col_total_kg * n_col_total / 1000
    g_col_kgm2  = G_col_all_t * 1000 / S_floor

    log.append(f"Колонны М1: ΣFв={ΣFv_kn:.0f} кН, ΣFн={ΣFn_kn:.0f} кН, "
               f"1 кол.={G_col_total_kg:.0f} кг, n={n_col_total}, "
               f"g={g_col_kgm2:.2f} кг/м²")

    res["колонны"] = {
        "метод": "1",
        "n_колонн": n_col_total,
        "ΣFv_кн": round(ΣFv_kn, 1),
        "ΣFn_кн": round(ΣFn_kn, 1),
        "масса_1_верх_кг": round(G_col_upper_kn / 9.81 * 1000, 1),
        "масса_1_низ_кг":  round(G_col_lower_kn / 9.81 * 1000, 1),
        "масса_1_общ_кг":  round(G_col_total_kg, 1),
        "расход_кгм2": round(g_col_kgm2, 2),
        "масса_общая_т": round(G_col_all_t, 2),
    }

    # ── 7. ФАХВЕРК (Метод 2) ─────────────────────────────
    g_fakh = get_fakhverk_kgm2(df_fakh, col_step, has_post, H_full, rig_load)
    if g_fakh is not None:
        G_fakh_total_t = g_fakh * S_walls / 1000
        res["фахверк"] = {
            "метод": "2",
            "расход_кгм2_стены": g_fakh,
            "площадь_стен_м2": round(S_walls, 1),
            "масса_общая_т": round(G_fakh_total_t, 2),
        }
        log.append(f"Фахверк: {g_fakh} кг/м² стены, S={S_walls:.0f} м²")
    else:
        res["фахверк"] = {"ошибка": "Не удалось определить"}

    # ── 8. ОГРАЖДАЮЩИЕ КОНСТРУКЦИИ ────────────────────────
    # Стены (периметр × высота)
    res["ограждение"] = {
        "стены_м2": round(S_walls, 1),
        "кровля_м2": round(S_floor, 1),
    }

    # ── 9. ОПОРЫ ТРУБОПРОВОДОВ (Метод 2) ──────────────────
    g_pipes = get_pipe_support_kgm2(df_fakh, bld_type)
    if g_pipes is not None:
        G_pipes_t = g_pipes * S_floor / 1000
        res["опоры_трубопроводов"] = {
            "метод": "2",
            "расход_кгм2": g_pipes,
            "масса_общая_т": round(G_pipes_t, 2),
        }
    else:
        res["опоры_трубопроводов"] = {"примечание": "Тип здания не определён"}

    # ── ИТОГ ─────────────────────────────────────────────
    def safe_float(d, *keys):
        for k in keys:
            v = d.get(k)
            if isinstance(v, (int, float)):
                return v
        return 0.0

    total_m1 = (
        safe_float(res["прогоны"], "масса_общая_т")
        + safe_float(res["фермы"], "масса_общая_т_М1")
        + safe_float(res.get("подстропильные_фермы", {}), "масса_общая_т_М1")
        + safe_float(res["подкрановые_балки"], "масса_общая_т_М1")
        + safe_float(res["колонны"], "масса_общая_т")
    )
    total_m2 = (
        safe_float(res["прогоны"], "масса_общая_т")  # прогоны только М1
        + safe_float(res["фермы"], "масса_общая_т_М2")
        + safe_float(res.get("подстропильные_фермы", {}), "масса_общая_т_М2")
        + safe_float(res["подкрановые_балки"], "масса_общая_т_М2")
        + safe_float(res["колонны"], "масса_общая_т")  # колонны только М1
        + safe_float(res["связи_покрытия"], "масса_общая_т")
        + safe_float(res.get("фахверк", {}), "масса_общая_т")
        + safe_float(res.get("опоры_трубопроводов", {}), "масса_общая_т")
    )

    res["итого"] = {
        "каркас_М1_т": round(total_m1, 2),
        "каркас_М2_т": round(total_m2, 2),
        "каркас_М1_кгм2": round(total_m1 * 1000 / S_floor, 2) if S_floor else 0,
        "каркас_М2_кгм2": round(total_m2 * 1000 / S_floor, 2) if S_floor else 0,
    }

    res["_log"] = log
    return res


# ─────────────────────────────────────────────────────────
#  GUI
# ─────────────────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FONT_LABEL  = ("Segoe UI", 13)
FONT_TITLE  = ("Segoe UI", 14, "bold")
FONT_RESULT = ("Consolas", 12)

PAD = {"padx": 8, "pady": 4}


class FloatEntry(ctk.CTkEntry):
    """Поле ввода числа с плавающей запятой."""

    def get_float(self, default=0.0):
        try:
            return float(self.get().replace(",", "."))
        except ValueError:
            return default


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Металлоемкость производственных зданий — v1.0")
        self.geometry("1400x900")
        self.resizable(True, True)

        self._build_ui()

    # ── Построение интерфейса ─────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # ── Левая панель: ввод ────────────────────────────
        left = ctk.CTkScrollableFrame(self, label_text="Входные параметры",
                                       width=500)
        left.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)

        r = 0

        def section(text):
            nonlocal r
            ctk.CTkLabel(left, text=text, font=FONT_TITLE,
                         text_color="#4fc3f7").grid(
                row=r, column=0, columnspan=2, sticky="w", **PAD)
            r += 1

        def row_entry(label, default="", tooltip=""):
            nonlocal r
            ctk.CTkLabel(left, text=label, font=FONT_LABEL).grid(
                row=r, column=0, sticky="w", **PAD)
            e = FloatEntry(left, width=120)
            e.insert(0, str(default))
            e.grid(row=r, column=1, sticky="w", **PAD)
            r += 1
            return e

        def row_combo(label, values, default=None):
            nonlocal r
            ctk.CTkLabel(left, text=label, font=FONT_LABEL).grid(
                row=r, column=0, sticky="w", **PAD)
            var = ctk.StringVar(value=default or values[0])
            cb  = ctk.CTkComboBox(left, values=values, variable=var, width=160)
            cb.grid(row=r, column=1, sticky="w", **PAD)
            r += 1
            return var

        def row_check(label, default=False):
            nonlocal r
            var = ctk.BooleanVar(value=default)
            cb  = ctk.CTkCheckBox(left, text=label, variable=var, font=FONT_LABEL)
            cb.grid(row=r, column=0, columnspan=2, sticky="w", **PAD)
            r += 1
            return var

        # ── Геометрия ─────────────────────────────────────
        section("Геометрия здания")
        self.e_L_build = row_entry("Длина здания по осям, м", 120)
        self.e_W_build = row_entry("Ширина здания, м", 48)
        self.e_L_span  = row_entry("Пролёт фермы L, м", 24)
        self.e_B_step  = row_entry("Шаг ферм B, м", 6)
        self.v_col_step = row_combo("Шаг колонн, м", ["6", "12"], "12")
        self.e_h_rail   = row_entry("Уровень головки рельса, м", 8.0)

        # ── Нагрузки ──────────────────────────────────────
        section("Нагрузки (расчётные, кН/м²)")
        self.e_Q_snow   = row_entry("Снег (Qснег), кН/м²", 2.1)
        self.e_Q_dust   = row_entry("Пыль (Qпыль), кН/м²", 0.0)
        self.e_Q_roof   = row_entry("Кровля (Qкровля), кН/м²", 0.65)
        self.e_Q_purlin = row_entry("Вес прогона (Qвес.прог.), кН/м²", 0.35)
        self.e_yc       = row_entry("Коэф. уровня ответственности γc", 1.0)

        # ── Тип фермы ─────────────────────────────────────
        section("Стропильные фермы")
        self.v_truss = row_combo("Тип фермы", ["Уголки", "Двутавры", "Молодечно"])

        # ── Кран ──────────────────────────────────────────
        section("Мостовой кран")
        self.e_crane_cap = row_entry("Грузоподъёмность крана, т", 50)
        self.v_n_cranes  = row_combo("Кол-во кранов в пролёте", ["1", "2"], "1")
        self.v_with_pass = row_combo("Тормозные пути",
                                     ["С проходом", "Без прохода"])

        # ── Фахверк ───────────────────────────────────────
        section("Фахверк")
        self.e_rig_load = row_entry("Нагрузка на ригели фахверка, кг/м.п.", 0)
        self.v_has_post = row_check("Наличие стойки фахверка (только при шаге 12 м)")

        # ── Тип здания ────────────────────────────────────
        section("Тип здания (для опор трубопроводов)")
        self.v_bld_type = row_combo(
            "Тип здания",
            ["Основные производственные", "Здания энергоносителей", "Вспомогательные здания"]
        )

        # ── Кнопки ────────────────────────────────────────
        r += 1
        btn_frame = ctk.CTkFrame(left, fg_color="transparent")
        btn_frame.grid(row=r, column=0, columnspan=2, pady=10)

        ctk.CTkButton(
            btn_frame, text="  Рассчитать", font=FONT_TITLE,
            command=self._on_calculate, fg_color="#1565c0", hover_color="#0d47a1",
            width=180, height=44
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Очистить", font=FONT_LABEL,
            command=self._on_clear, fg_color="#37474f", hover_color="#263238",
            width=100, height=44
        ).pack(side="left", padx=5)

        # Подсветка стойки фахверка (только при шаге 12м)
        def _toggle_post(*_):
            step = self.v_col_step.get()
            self.v_has_post.set(False)
        self.v_col_step.trace_add("write", _toggle_post)

        # ── Правая панель: результаты ─────────────────────
        right = ctk.CTkFrame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Результаты расчёта",
                     font=FONT_TITLE).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

        self.txt_result = ctk.CTkTextbox(right, font=FONT_RESULT,
                                          wrap="word", state="disabled")
        self.txt_result.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))

        # Строка статуса
        self.lbl_status = ctk.CTkLabel(self, text="", font=FONT_LABEL,
                                        text_color="#80cbc4")
        self.lbl_status.grid(row=1, column=0, columnspan=2,
                              sticky="w", padx=20, pady=(0, 8))

    # ── Чтение параметров из UI ──────────────────────────

    def _read_params(self) -> dict:
        col_step = int(self.v_col_step.get())
        has_post = self.v_has_post.get() and col_step == 12
        return {
            "L_build":    self.e_L_build.get_float(120),
            "W_build":    self.e_W_build.get_float(48),
            "L_span":     self.e_L_span.get_float(24),
            "B_step":     self.e_B_step.get_float(6),
            "col_step":   col_step,
            "h_rail":     self.e_h_rail.get_float(8),
            "Q_snow":     self.e_Q_snow.get_float(2.1),
            "Q_dust":     self.e_Q_dust.get_float(0.0),
            "Q_roof":     self.e_Q_roof.get_float(0.65),
            "Q_purlin":   self.e_Q_purlin.get_float(0.35),
            "yc":         self.e_yc.get_float(1.0),
            "truss_type": self.v_truss.get(),
            "q_crane_t":  self.e_crane_cap.get_float(50),
            "n_cranes":   int(self.v_n_cranes.get()),
            "with_pass":  self.v_with_pass.get() == "С проходом",
            "rig_load":   self.e_rig_load.get_float(0),
            "has_post":   has_post,
            "bld_type":   self.v_bld_type.get(),
        }

    # ── Кнопка: Рассчитать ───────────────────────────────

    def _on_calculate(self):
        self.lbl_status.configure(text="Выполняется расчёт…", text_color="#ffcc80")
        self.update()
        try:
            params = self._read_params()
            res    = calculate(params)
            self._show_results(params, res)
            self.lbl_status.configure(
                text="Расчёт завершён успешно.", text_color="#80cbc4"
            )
        except FileNotFoundError as e:
            messagebox.showerror("Файлы не найдены", str(e))
            self.lbl_status.configure(text="Ошибка: файлы не найдены.", text_color="#ef9a9a")
        except Exception:
            tb = traceback.format_exc()
            messagebox.showerror("Ошибка расчёта", tb)
            self.lbl_status.configure(text="Ошибка расчёта.", text_color="#ef9a9a")

    def _on_clear(self):
        self._set_result("")
        self.lbl_status.configure(text="")

    # ── Форматирование и отображение результатов ─────────

    def _set_result(self, text: str):
        self.txt_result.configure(state="normal")
        self.txt_result.delete("1.0", "end")
        self.txt_result.insert("1.0", text)
        self.txt_result.configure(state="disabled")

    def _show_results(self, params: dict, res: dict):
        lines = []
        sep  = "─" * 68

        def h(text):
            lines.append(f"\n{sep}")
            lines.append(f"  {text}")
            lines.append(sep)

        def row(label, *vals):
            label_s = f"  {label:<42}"
            vals_s  = "  ".join(str(v) for v in vals)
            lines.append(f"{label_s}  {vals_s}")

        def row2(label, m1, m2):
            lines.append(f"  {label:<42}  М1: {m1:<12}  М2: {m2}")

        # ── Заголовок ─────────────────────────────────────
        lines.append("=" * 68)
        lines.append("  РАСЧЁТ МЕТАЛЛОЁМКОСТИ ПРОИЗВОДСТВЕННОГО ЗДАНИЯ")
        lines.append(f"  Шаг колонн: {params['col_step']} м  |  "
                     f"Пролёт фермы: {params['L_span']} м  |  "
                     f"Тип фермы: {params['truss_type']}")
        lines.append(f"  Кран: {params['q_crane_t']} т  |  "
                     f"Кранов: {params['n_cranes']}  |  "
                     f"{'С проходом' if params['with_pass'] else 'Без прохода'}")
        lines.append("=" * 68)

        # ── Геометрия ─────────────────────────────────────
        h("ГЕОМЕТРИЯ")
        row("Длина здания, м:", params["L_build"])
        row("Ширина здания, м:", params["W_build"])
        row("Площадь пола, м²:", params["L_build"] * params["W_build"])
        row("Высота здания (ориент.), м:", f"~{round(params['h_rail'] + 1.5, 1)} (уточн. в логе)")

        # ── Прогоны ───────────────────────────────────────
        h("1. ПРОГОНЫ  [Метод 1]")
        pr = res["прогоны"]
        row("Расчётная нагрузка, т/м:", pr["нагрузка_тм"])
        row("Подобранный профиль:", pr["профиль"])
        row("Масса 1 прогона, кг:", pr["масса_1шт_кг"])
        row("Количество в 1 шаге ферм:", pr["n_в_шаге"])
        row("Расход, кг/м²:", pr["расход_кгм2"])
        row("Масса ИТОГО, т:", pr["масса_общая_т"])

        # ── Фермы ─────────────────────────────────────────
        h("2. СТРОПИЛЬНЫЕ ФЕРМЫ  [М1 + М2]")
        fm = res["фермы"]
        row("Нагрузка на ферму, т/м:", fm["нагрузка_тм"])
        row2("Расход, кг/м²:", fm["М1_расход_кгм2"], fm["М2_расход_кгм2"])
        row2("Масса ИТОГО, т:", fm["масса_общая_т_М1"], fm["масса_общая_т_М2"])

        # ── Связи ─────────────────────────────────────────
        h("3. СВЯЗИ ПОКРЫТИЯ  [Метод 2]")
        sv = res["связи_покрытия"]
        row("Расход, кг/м²:", sv["расход_кгм2"])
        row("Масса ИТОГО, т:", sv["масса_общая_т"])

        # ── Подстропильные ────────────────────────────────
        h("4. ПОДСТРОПИЛЬНЫЕ ФЕРМЫ  [М1 + М2]")
        psf = res.get("подстропильные_фермы", {})
        if "примечание" in psf:
            row(psf["примечание"])
        else:
            row("Реакция R, кН:", psf["R_кн"])
            row("Реакция R, т:", psf["R_т"])
            row("Коэф. αпф:", psf["alpha_pf"])
            row2("Расход, кг/м²:", psf["М1_расход_кгм2"], psf["М2_расход_кгм2"])
            row2("Масса ИТОГО, т:", psf["масса_общая_т_М1"], psf["масса_общая_т_М2"])

        # ── Подкрановые балки ─────────────────────────────
        h("5. ПОДКРАНОВЫЕ БАЛКИ  [М1 + М2]")
        pb = res["подкрановые_балки"]
        row("Коэф. αпб:", pb["alpha_pb"])
        row("Вес рельса qр, кН/м:", pb["q_rail_кнм"])
        row("Пролёт п/б, м:", pb["L_pb_м"])
        row("Масса 1 балки (М1), т:", pb["G_1пб_t_М1"])
        row("Таблица: крайний ряд балки, кг/м:", pb["кг/м_крайн"])
        row("Таблица: средний ряд балки, кг/м:", pb["кг/м_сред"])
        row("Таблица: тормоза крайний, кг/м:", pb["тормоз_кгм_крайн"])
        row("Таблица: тормоза средний, кг/м:", pb["тормоз_кгм_сред"])
        row2("Расход, кг/м²:", pb["М1_расход_кгм2"], pb["М2_расход_кгм2"])
        row2("Масса ИТОГО, т:", pb["масса_общая_т_М1"], pb["масса_общая_т_М2"])

        # ── Колонны ───────────────────────────────────────
        h("6. КОЛОННЫ  [Метод 1]")
        kl = res["колонны"]
        row("Количество колонн:", kl["n_колонн"])
        row("ΣFв (надкрановая), кН:", kl["ΣFv_кн"])
        row("ΣFн (подкрановая), кН:", kl["ΣFn_кн"])
        row("Масса 1 кол. верхняя, кг:", kl["масса_1_верх_кг"])
        row("Масса 1 кол. нижняя, кг:", kl["масса_1_низ_кг"])
        row("Масса 1 колонны общая, кг:", kl["масса_1_общ_кг"])
        row("Расход, кг/м²:", kl["расход_кгм2"])
        row("Масса ИТОГО, т:", kl["масса_общая_т"])

        # ── Фахверк ───────────────────────────────────────
        h("7. ФАХВЕРК  [Метод 2]")
        fh = res.get("фахверк", {})
        if "ошибка" in fh:
            row("Ошибка:", fh["ошибка"])
        else:
            row("Расход, кг/м² площади стен:", fh.get("расход_кгм2_стены", "н/п"))
            row("Площадь стен, м²:", fh.get("площадь_стен_м2", "н/п"))
            row("Масса ИТОГО, т:", fh.get("масса_общая_т", "н/п"))

        # ── Ограждение ────────────────────────────────────
        h("8. ОГРАЖДАЮЩИЕ КОНСТРУКЦИИ (справочно)")
        og = res["ограждение"]
        row("Площадь стен (периметр × высота), м²:", og["стены_м2"])
        row("Площадь кровли (длина × ширина), м²:",  og["кровля_м2"])

        # ── Опоры трубопроводов ───────────────────────────
        h("9. ОПОРЫ ТРУБОПРОВОДОВ  [Метод 2]")
        op = res.get("опоры_трубопроводов", {})
        if "примечание" in op:
            row(op["примечание"])
        else:
            row("Расход, кг/м²:", op.get("расход_кгм2", "н/п"))
            row("Масса ИТОГО, т:", op.get("масса_общая_т", "н/п"))

        # ── Итог ──────────────────────────────────────────
        lines.append("\n" + "=" * 68)
        lines.append("  ИТОГО ПО КАРКАСУ")
        lines.append("=" * 68)
        it = res["итого"]
        lines.append(f"  {'Метод 1 (формулы):':<44}  {it['каркас_М1_т']} т  "
                     f"({it['каркас_М1_кгм2']} кг/м²)")
        lines.append(f"  {'Метод 2 (таблицы):':<44}  {it['каркас_М2_т']} т  "
                     f"({it['каркас_М2_кгм2']} кг/м²)")
        lines.append("=" * 68)

        # ── Лог ───────────────────────────────────────────
        if res.get("_log"):
            lines.append("\n─── Внутренний лог ──────────────────────────────────────────────")
            for entry in res["_log"]:
                lines.append(f"  {entry}")

        self._set_result("\n".join(lines))


# ─────────────────────────────────────────────────────────
#  ТОЧКА ВХОДА
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
