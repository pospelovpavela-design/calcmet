#!/usr/bin/env python3
"""
Расчётный модуль металлоёмкости производственных зданий с мостовыми кранами.
Метод 1 — эмпирические формулы.
Метод 2 — таблицы (вшиты в код, внешние файлы не требуются).
"""

import os
import sys
import math
import traceback
import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk

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

# Коэффициент αпб для подкрановых балок по г/п крана (кН/м/м)
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
    5:   0.461,
    10:  0.461,
    20:  0.461,
    32:  0.598,
    50:  0.598,
    80:  0.831,
    100: 1.135,
    125: 1.135,
    200: 1.135,
    320: 1.417,
    400: 1.417,
}

# Высота балки (отн. Lпб): (г/п: hб/Lпб при шаге 6м, при 12м)
BEAM_HEIGHT_RATIO = {
    20:  (1/7,   1/9),
    32:  (1/7,   1/9),
    50:  (1/6,   1/8.5),
    80:  (1/6,   1/7.5),
    100: (1/6,   1/7),
    125: (1/6,   1/7),
    160: (1/6,   1/7),
    200: (1/6,   1/7),
}

# Нормативные эквивалентные нагрузки q (кН/м) по г/п крана
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

# ─────────────────────────────────────────────────────────
#  HARDCODED ТАБЛИЦЫ (Метод 2)
# ─────────────────────────────────────────────────────────

# Нагрузки для таблиц ферм (т/м.п.)
TRUSS_LOADS = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0,
               6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5,
               11.0, 11.5, 12.0, 12.5]

# Масса 1 стропильной фермы (т) по типу и пролёту
# Источник: металлоекмсоть покрытия.xlsx
TRUSS_MASSES = {
    "Уголки": {
        36: [5.90, 7.54, 10.37, 11.12, 12.30, 12.74, 13.30, 14.74, 15.66,
             15.66, 18.89, 18.89, 18.89, 19.30, 21.50, 21.50, 22.52, 23.70,
             24.57, 24.57, 26.30, 26.92],
        30: [5.20, 5.97, 6.47, 7.14, 7.14, 7.70, 9.00, 9.00, 10.20,
             10.20, 10.53, 11.64, 13.63, 13.63, 14.43, 14.43, 15.25, 15.25,
             16.43, 16.43, 16.43, 17.27],
        24: [2.30, 3.16, 3.94, 3.97, 4.29, 5.75, 5.75, 6.28, 6.28,
             6.28, 6.53, 6.53, 6.90, 7.97, 8.87, 8.87, 8.87, 8.87,
             8.87, 9.11, 10.45, 11.24],
        18: [2.16, 2.16, 2.34, 2.45, 2.68, 2.68, 2.83, 2.91, 3.17,
             3.64, 3.64, 3.77, 3.95, 3.95, 4.10, 4.10, 4.51, 4.51,
             4.51, 5.26, 5.26, 5.26],
    },
    "Двутавры": {
        36: [9.60, 10.20, 10.20, 11.47, 12.50, 13.49, 15.14, 15.28, 15.87,
             17.18, 18.72, 21.06, 21.06, 21.06, 22.11, 22.11, 25.52, 25.52,
             30.78, 31.66, 31.66, 31.85],
        30: [6.27, 6.38, 6.38, 8.07, 8.23, 8.90, 9.84, 9.93, 10.35,
             12.99, 12.99, 12.99, 12.99, 14.89, 14.89, 14.89, 15.35, 18.68,
             18.68, 18.68, 19.69, 19.69],
        24: [4.60, 4.60, 5.19, 5.30, 5.79, 5.79, 6.35, 6.63, 7.48,
             8.31, 8.31, 8.47, 8.47, 8.63, 9.30, 9.30, 11.08, 11.08,
             11.08, 11.08, 11.08, 12.10],
        18: [2.92, 2.92, 2.92, 2.92, 3.37, 3.92, 3.92, 3.92, 4.34,
             4.34, 4.34, 4.72, 4.72, 4.72, 4.72, 4.72, 5.42, 5.42,
             5.49, 5.49, 5.86, 5.86],
    },
    "Молодечно": {
        36: [7.00, 8.05, 9.20, 12.25, 13.53, 13.53, 15.96, 17.18, 17.61,
             21.26, 21.26, 23.01, 24.25, 29.80, 29.80, 29.80, 29.80, 29.80,
             31.57, 37.40, 37.40, 37.40],
        30: [5.24, 5.80, 5.80, 7.34, 7.34, 11.55, 10.40, 11.97, 11.97,
             13.59, 13.59, 13.59, 15.40, 16.22, 17.70, 19.54, 19.54, 19.54,
             21.37, 21.37, 21.37, 21.37],
        24: [2.48, 3.60, 3.85, 4.11, 5.07, 5.07, 6.18, 6.24, 6.47,
             8.02, 8.02, 8.70, 9.37, 9.37, 10.00, 10.90, 10.90, 11.54,
             11.54, 12.37, 13.62, 13.62],
        18: [1.29, 1.54, 1.58, 2.07, 2.18, 2.65, 3.40, 3.40, 3.40,
             3.40, 4.08, 4.08, 4.08, 4.70, 4.83, 4.83, 5.70, 6.07,
             6.07, 6.07, 6.07, 7.08],
    },
}

# Подстропильные фермы: нагрузка (т) → масса 1 фермы (т)
# Источник: металлоекмсоть покрытия.xlsx
SUBTRUSS_LOADS  = [18.0, 36.0, 54.0, 72.0, 81.0, 108.0, 126.0, 144.0,
                   162.0, 180.0, 198.0, 216.0, 234.0, 255.0]
SUBTRUSS_MASSES = [1.57, 2.22, 2.31, 2.72, 2.72, 4.59, 5.32, 5.32,
                   5.70, 5.80, 6.30, 6.30, 6.53, 6.71]

# Фахверк: (тип, категория нагрузки, категория высоты) → кг/м² стены
# тип: 'I' (пролёт 6м без стойки), 'II' (пролёт 12м без стойки), 'III' (пролёт 6м со стойкой)
# нагрузка: 0=без нагрузки, 1=100 кг/м.п., 2=300 кг/м.п.
# высота: 0=до 10м, 1=до 20м, 2=до 40м
# Источник: Металлоёмкость фахверк.xlsx (лист Расчеты)
FAKHVERK_DATA = {
    ('I',   0, 0):  9,  ('I',   0, 1): 10, ('I',   0, 2): 11,
    ('I',   1, 0):  9,  ('I',   1, 1): 11, ('I',   1, 2): 11,
    ('I',   2, 0): 10,  ('I',   2, 1): 12, ('I',   2, 2): 12,
    ('II',  0, 0): 23,  ('II',  0, 1): 25, ('II',  0, 2): 25,
    ('II',  1, 0): 23,  ('II',  1, 1): 25, ('II',  1, 2): 25,
    ('II',  2, 0): 26,  ('II',  2, 1): 30, ('II',  2, 2): 30,
    ('III', 0, 0): 19,  ('III', 0, 1): 28, ('III', 0, 2): 45,
    ('III', 1, 0): 19,  ('III', 1, 1): 29, ('III', 1, 2): 46,
    ('III', 2, 0): 20,  ('III', 2, 1): 30, ('III', 2, 2): 48,
}

# Подкрановые балки: значения кг/м по позиции
# Индекс: q_order[i]*2 + (0 если 1 кран, 1 если 2 крана)
# Источник: Таблица металлоемкости на подкрановые конструкции.docx
_CB_Q1 = [5, 10, 20, 32, 50]      # г/п для таблицы 1
_CB_Q2 = [80, 100, 125, 200, 400]  # г/п для таблицы 2

CRANE_BEAM_T1 = {   # г/п 5–50 т
    6:  [80, 85, 90, 190, 200, 100, 240, 250, 105, 140],
    12: [150, 160, 320, 350, 180, 200, 390, 440, 220, 470],
}
CRANE_BEAM_T2 = {   # г/п 80–400 т
    12: [290, 320, 380, 940,  980, 300,  330, 500, 350, 540],
    18: [460, 480, 500, 1020, 1080, 490, 520, 540, 1120, 1180],
    24: [680, 720, 780, 1040, 1120, 820, 920, 1620, 1840, 880],
}

# Тормозные конструкции: (пролёт, крайний ряд, с проходом) → [val_1к, val_2к]
# Источник: Таблица металлоемкости на тормозные конструкции.docx
BRAKE_T1 = {   # г/п 5–50 т
    (6,  True,  True):  [100, 110],
    (6,  True,  False): [65,  70],
    (6,  False, True):  [120, 140],
    (6,  False, False): [70,  75],
    (12, True,  True):  [100, 120],
    (12, True,  False): [65,  70],
    (12, False, True):  [100, 120],
    (12, False, False): [70,  75],
}
BRAKE_T2 = {   # г/п 80–400 т
    (12, True,  True):  [120, 140],
    (12, True,  False): [80,  100],
    (12, False, True):  [140, 160],
    (12, False, False): [60,  80],
    (18, True,  True):  [120, 140],
    (18, True,  False): [80,  100],
    (18, False, True):  [140, 160],
    (18, False, False): [80,  100],
    (24, True,  True):  [220, 240],
    (24, True,  False): [140, 160],
    (24, False, True):  [220, 240],
    (24, False, False): [140, 160],
}

# ─────────────────────────────────────────────────────────
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ─────────────────────────────────────────────────────────

def closest_alpha_pb(q_kn: float) -> float:
    caps = sorted(CRANE_BEAM_ALPHA.keys())
    for cap in caps:
        if q_kn <= cap:
            return CRANE_BEAM_ALPHA[cap]
    return CRANE_BEAM_ALPHA[caps[-1]]


def rail_weight(q_kn: float) -> float:
    caps = sorted(RAIL_WEIGHT_KN.keys())
    for cap in caps:
        if q_kn <= cap:
            return RAIL_WEIGHT_KN[cap]
    return RAIL_WEIGHT_KN[caps[-1]]


def q_equiv(q_kn: float) -> float:
    caps = sorted(CRANE_Q_EQUIV.keys())
    for cap in caps:
        if q_kn <= cap:
            return CRANE_Q_EQUIV[cap]
    return CRANE_Q_EQUIV[caps[-1]]


def select_purlin(load_tm: float, span_m: float):
    for max_load, mass_6, mass_12, name in PURLIN_TABLE:
        if load_tm <= max_load:
            mass = mass_6 if span_m <= 6 else mass_12
            return mass, name
    _, mass_6, mass_12, name = PURLIN_TABLE[-1]
    mass = mass_6 if span_m <= 6 else mass_12
    return mass, f"{name} (нагрузка превышает таблицу!)"


def interp_table(loads, masses, target):
    for i, ld in enumerate(loads):
        if target <= ld:
            return masses[i]
    return masses[-1]


def ceil_to_table(target, values):
    for v in sorted(values):
        if target <= v:
            return v
    return sorted(values)[-1]


# ─────────────────────────────────────────────────────────
#  ФУНКЦИИ ТАБЛИЦ (Метод 2) — все данные вшиты в код
# ─────────────────────────────────────────────────────────

def get_truss_mass_m2(truss_type: str, span_m: float, load_tm: float) -> tuple:
    """Масса 1 стропильной фермы (т) из встроенной таблицы."""
    spans_avail = sorted(TRUSS_MASSES.get(truss_type, {}).keys())
    if not spans_avail:
        return None, f"Тип фермы '{truss_type}' не найден"
    span_key = ceil_to_table(span_m, spans_avail)
    masses = TRUSS_MASSES[truss_type].get(span_key)
    if masses is None:
        return None, f"Пролёт {span_m}м не найден"
    mass = interp_table(TRUSS_LOADS, masses, load_tm)
    return mass, f"{truss_type} пролёт {span_key}м"


def get_subtruss_mass_m2(R_t: float) -> float:
    """Масса 1 подстропильной фермы (т) из встроенной таблицы."""
    R_ceil = ceil_to_table(R_t, SUBTRUSS_LOADS)
    return interp_table(SUBTRUSS_LOADS, SUBTRUSS_MASSES, R_ceil)


def get_bracing_kgm2(q_crane_t: float, step_farm_m: float) -> float:
    """Расход стали на связи покрытия (кг/м²)."""
    if q_crane_t <= 120:
        return 15.0 if step_farm_m <= 6 else 35.0
    else:
        return 40.0 if step_farm_m <= 6 else 55.0


def get_crane_beam_kgm_m2(q_crane_t: float, span_pb_m: float, n_cranes: int):
    """Металлоёмкость подкрановой балки (кг/м) из встроенной таблицы."""
    try:
        if q_crane_t <= 50:
            table  = CRANE_BEAM_T1
            q_ord  = _CB_Q1
        else:
            table  = CRANE_BEAM_T2
            q_ord  = _CB_Q2

        # Выбрать ближайший пролёт из таблицы
        spans = sorted(table.keys())
        span_key = ceil_to_table(span_pb_m, spans)
        vals = table.get(span_key)
        if vals is None:
            return None

        q_idx    = min(range(len(q_ord)), key=lambda i: abs(q_ord[i] - q_crane_t))
        c_idx    = q_idx * 2 + (0 if n_cranes == 1 else 1)
        if c_idx < len(vals):
            return vals[c_idx]
    except Exception as e:
        print(f"Ошибка подкрановой балки: {e}")
    return None


def get_brake_kgm(q_crane_t: float, span_pb_m: float, n_cranes: int,
                  with_passage: bool, is_edge: bool):
    """Металлоёмкость тормозных конструкций (кг/м) из встроенной таблицы."""
    try:
        table = BRAKE_T1 if q_crane_t <= 50 else BRAKE_T2
        spans = sorted({k[0] for k in table})
        span_key = ceil_to_table(span_pb_m, spans)
        vals = table.get((span_key, is_edge, with_passage))
        if vals is None:
            # Fallback — ближайший ключ
            for k, v in table.items():
                if k[0] == span_key:
                    vals = v
                    break
        if vals:
            idx = 0 if n_cranes == 1 else min(1, len(vals) - 1)
            return vals[idx]
    except Exception as e:
        print(f"Ошибка тормозных конструкций: {e}")
    return None


def get_fakhverk_kgm2(step_col_m: float, has_fakhverk_post: bool,
                      h_building: float, rig_load: float):
    """Расход стали на фахверк (кг/м² стен) из встроенной таблицы."""
    try:
        if step_col_m <= 6 and has_fakhverk_post:
            ftype = 'III'
        elif step_col_m <= 6:
            ftype = 'I'
        else:
            ftype = 'II'

        if rig_load <= 0:
            load_cat = 0
        elif rig_load <= 100:
            load_cat = 1
        else:
            load_cat = 2

        if h_building <= 10:
            h_cat = 0
        elif h_building <= 20:
            h_cat = 1
        else:
            h_cat = 2

        return FAKHVERK_DATA.get((ftype, load_cat, h_cat))
    except Exception as e:
        print(f"Ошибка фахверк: {e}")
        return None


def get_pipe_support_kgm2(building_type: str):
    """Расход стали на опоры трубопроводов (кг/м²) из встроенной таблицы."""
    type_map = {
        "Основные производственные":  (11, 22),
        "Здания энергоносителей":      (23, 40),
        "Вспомогательные здания":      (2,  4),
    }
    rng = type_map.get(building_type, (11, 22))
    return (rng[0] + rng[1]) / 2


# ─────────────────────────────────────────────────────────
#  ОСНОВНАЯ ЛОГИКА РАСЧЁТА
# ─────────────────────────────────────────────────────────

def calculate(params: dict) -> dict:
    res = {}
    log = []

    # ── Входные параметры ──────────────────────────────────
    L_build    = params["L_build"]
    W_build    = params["W_build"]
    L_span     = params["L_span"]
    B_step     = params["B_step"]
    col_step   = params["col_step"]
    h_rail     = params["h_rail"]
    Q_snow     = params["Q_snow"]
    Q_dust     = params["Q_dust"]
    Q_roof     = params["Q_roof"]
    Q_purlin   = params["Q_purlin"]
    yc         = params["yc"]
    truss_type = params["truss_type"]
    q_crane_t  = params["q_crane_t"]
    n_cranes   = params["n_cranes"]
    with_pass  = params["with_pass"]
    rig_load   = params["rig_load"]
    has_post   = params["has_post"]
    bld_type   = params["bld_type"]

    # ── Геометрия ─────────────────────────────────────────
    S_floor  = L_build * W_build
    P_walls  = 2 * (L_build + W_build)
    H_lower  = h_rail

    H_full_est = h_rail + 1.5
    S_walls_est = P_walls * H_full_est

    log.append(f"Площадь пола: {S_floor:.1f} м²")

    # ── 1. ПРОГОНЫ (Метод 1) ──────────────────────────────
    step_purlin = 3.0
    q_pr_knm  = (Q_roof + Q_purlin + Q_snow + Q_dust) * step_purlin * yc
    q_pr_tm   = q_pr_knm / 9.81

    mass_purlin, purlin_name = select_purlin(q_pr_tm, B_step)
    n_pr = L_span / step_purlin + 3
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
    g_links_est = 0.05
    gn_total    = Q_snow + Q_dust + Q_roof + Q_purlin + g_links_est
    Q_total_knm = gn_total * B_step * yc
    Q_total_tm  = Q_total_knm / 9.81

    g_truss_m1 = None
    g_truss_m2 = None

    if truss_type == "Уголки":
        alpha_f = 1.4
        gamma_n = yc
        G_truss_m1_kn = (gn_total * B_step / 1000 + 0.018) * alpha_f * L_span**2 / 0.85 * gamma_n
        G_truss_m1_t  = G_truss_m1_kn / 9.81
        n_trusses = (L_build / B_step + 1)
        g_truss_m1 = G_truss_m1_t * 1000 * n_trusses / S_floor
        log.append(f"Ферма М1: Gф={G_truss_m1_t*1000:.0f} кг, "
                   f"g={g_truss_m1:.2f} кг/м²")

    mass_truss_t, truss_label = get_truss_mass_m2(truss_type, L_span, Q_total_tm)
    if mass_truss_t is not None:
        n_trusses  = (L_build / B_step + 1)
        g_truss_m2 = mass_truss_t * 1000 * n_trusses / S_floor
        log.append(f"Ферма М2: 1 ферма={mass_truss_t*1000:.0f} кг "
                   f"(нагрузка {Q_total_tm:.2f} т/м), g={g_truss_m2:.2f} кг/м²")
    else:
        log.append(f"Ферма М2: {truss_label}")

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
        R_kn = Q_total_knm * L_span / 2
        R_t  = R_kn / 9.81

        R_for_alpha = max(100, min(R_kn, 400))
        alpha_pf    = (R_for_alpha - 100) * 0.0002 + 0.044
        Lpf         = 12.0
        G_sub_m1_t  = alpha_pf * Lpf**2
        n_sub = (L_build / col_step) * (W_build / L_span - 1) if W_build > L_span else 0
        if n_sub <= 0:
            n_sub = L_build / col_step
        g_sub_m1 = G_sub_m1_t * 1000 * n_sub / S_floor

        mass_sub_t = get_subtruss_mass_m2(R_t)
        if mass_sub_t is not None:
            g_sub_m2 = mass_sub_t * 1000 * n_sub / S_floor

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
    alpha_pb = closest_alpha_pb(q_crane_t)
    qr       = rail_weight(q_crane_t)
    k_pb     = 1.4
    L_pb     = float(col_step)

    G_pb_kn     = (alpha_pb * L_pb + qr) * L_pb * k_pb
    alpha_pb_t  = alpha_pb / 9.81
    G_pb_t      = (alpha_pb_t * L_pb + qr / 9.81) * L_pb * k_pb

    n_bays_along = math.ceil(L_build / col_step)
    n_rows_edge  = 2
    n_rows_mid   = max(0, round(W_build / L_span) - 1)
    n_pb_total   = (n_rows_edge + n_rows_mid * 2) * n_bays_along

    G_pb_total_m1_t = G_pb_t * n_pb_total
    g_pb_m1         = G_pb_total_m1_t * 1000 / S_floor

    pb_edge_kgm = get_crane_beam_kgm_m2(q_crane_t, L_pb, n_cranes)
    br_edge_kgm = get_brake_kgm(q_crane_t, L_pb, n_cranes, with_pass, is_edge=True)
    pb_mid_kgm  = get_crane_beam_kgm_m2(q_crane_t, L_pb, n_cranes)
    br_mid_kgm  = get_brake_kgm(q_crane_t, L_pb, n_cranes, with_pass, is_edge=False)

    if pb_edge_kgm and br_edge_kgm is not None:
        total_edge_kgm  = pb_edge_kgm + (br_edge_kgm or 0)
        total_mid_kgm   = (pb_mid_kgm or 0) + (br_mid_kgm or 0)
        G_pb_edge_t     = total_edge_kgm * L_pb * n_bays_along * n_rows_edge / 1000
        G_pb_mid_t      = total_mid_kgm  * L_pb * n_bays_along * n_rows_mid  / 1000
        G_pb_total_m2_t = G_pb_edge_t + G_pb_mid_t
        g_pb_m2         = G_pb_total_m2_t * 1000 / S_floor
    else:
        G_pb_total_m2_t = None
        g_pb_m2         = None

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
    rho       = 78.5
    Ry        = 24.0
    psi_upper = 1.4
    psi_lower = 2.1
    kM_upper  = 0.275
    kM_lower  = 0.45

    hb_ratio = BEAM_HEIGHT_RATIO.get(
        min(BEAM_HEIGHT_RATIO.keys(), key=lambda k: abs(k - q_crane_t)),
        (1/7, 1/9)
    )
    h_pb     = col_step * (hb_ratio[0] if col_step <= 6 else hb_ratio[1])
    h_rail_h = 0.12
    H_upper  = max(1.5, h_pb + h_rail_h + 0.3)
    H_lower  = h_rail

    H_full  = H_upper + H_lower
    S_walls = P_walls * H_full

    log.append(f"Высота здания (ориент.): {H_full:.1f} м "
               f"(надкр.={H_upper:.1f}, подкр.={H_lower:.1f})")
    log.append(f"Площадь стен: {S_walls:.1f} м²")

    gst         = 0.25
    alpha_win   = 0.15
    G_wall_upper_kn = gst * H_upper * (1 - alpha_win) * col_step
    G_wall_lower_kn = gst * H_lower * (1 - alpha_win) * col_step

    ΣFv_kn = (Q_roof + Q_purlin + Q_snow + Q_dust) * col_step * L_span / 2 + G_wall_upper_kn
    G_col_upper_kn = ΣFv_kn * rho * psi_upper * H_upper / (kM_upper * 24000)

    k1       = 1.1
    q_eq     = q_equiv(q_crane_t)
    D_max_kn = q_eq * col_step * k1 * yc

    ΣFn_kn = ΣFv_kn + D_max_kn + G_pb_kn + G_wall_lower_kn + G_col_upper_kn
    G_col_lower_kn = ΣFn_kn * rho * psi_lower * H_lower / (kM_lower * 24000)

    G_col_total_kn = G_col_upper_kn + G_col_lower_kn
    G_col_total_kg = G_col_total_kn / 9.81 * 1000

    n_col_along = round(L_build / col_step) + 1
    n_rows      = round(W_build / L_span) + 1
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
    g_fakh = get_fakhverk_kgm2(col_step, has_post, H_full, rig_load)
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
    res["ограждение"] = {
        "стены_м2": round(S_walls, 1),
        "кровля_м2": round(S_floor, 1),
    }

    # ── 9. ОПОРЫ ТРУБОПРОВОДОВ (Метод 2) ──────────────────
    g_pipes = get_pipe_support_kgm2(bld_type)
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
        safe_float(res["прогоны"], "масса_общая_т")
        + safe_float(res["фермы"], "масса_общая_т_М2")
        + safe_float(res.get("подстропильные_фермы", {}), "масса_общая_т_М2")
        + safe_float(res["подкрановые_балки"], "масса_общая_т_М2")
        + safe_float(res["колонны"], "масса_общая_т")
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
    def get_float(self, default=0.0):
        try:
            return float(self.get().replace(",", "."))
        except ValueError:
            return default


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Металлоёмкость производственных зданий — v1.0")
        self.geometry("1400x900")
        self.resizable(True, True)
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

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

        def row_entry(label, default=""):
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

        section("Геометрия здания")
        self.e_L_build  = row_entry("Длина здания по осям, м", 120)
        self.e_W_build  = row_entry("Ширина здания, м", 48)
        self.e_L_span   = row_entry("Пролёт фермы L, м", 24)
        self.e_B_step   = row_entry("Шаг ферм B, м", 6)
        self.v_col_step = row_combo("Шаг колонн, м", ["6", "12"], "12")
        self.e_h_rail   = row_entry("Уровень головки рельса, м", 8.0)

        section("Нагрузки (расчётные, кН/м²)")
        self.e_Q_snow   = row_entry("Снег (Qснег), кН/м²", 2.1)
        self.e_Q_dust   = row_entry("Пыль (Qпыль), кН/м²", 0.0)
        self.e_Q_roof   = row_entry("Кровля (Qкровля), кН/м²", 0.65)
        self.e_Q_purlin = row_entry("Вес прогона (Qвес.прог.), кН/м²", 0.35)
        self.e_yc       = row_entry("Коэф. уровня ответственности γc", 1.0)

        section("Стропильные фермы")
        self.v_truss = row_combo("Тип фермы", ["Уголки", "Двутавры", "Молодечно"])

        section("Мостовой кран")
        self.e_crane_cap = row_entry("Грузоподъёмность крана, т", 50)
        self.v_n_cranes  = row_combo("Кол-во кранов в пролёте", ["1", "2"], "1")
        self.v_with_pass = row_combo("Тормозные пути",
                                     ["С проходом", "Без прохода"])

        section("Фахверк")
        self.e_rig_load = row_entry("Нагрузка на ригели фахверка, кг/м.п.", 0)
        self.v_has_post = row_check("Наличие стойки фахверка (только при шаге 12 м)")

        section("Тип здания (для опор трубопроводов)")
        self.v_bld_type = row_combo(
            "Тип здания",
            ["Основные производственные", "Здания энергоносителей",
             "Вспомогательные здания"]
        )

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

        def _toggle_post(*_):
            self.v_has_post.set(False)
        self.v_col_step.trace_add("write", _toggle_post)

        right = ctk.CTkFrame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Результаты расчёта",
                     font=FONT_TITLE).grid(row=0, column=0, sticky="w",
                                           padx=10, pady=(10, 0))

        self.txt_result = ctk.CTkTextbox(right, font=FONT_RESULT,
                                          wrap="word", state="disabled")
        self.txt_result.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))

        self.lbl_status = ctk.CTkLabel(self, text="", font=FONT_LABEL,
                                        text_color="#80cbc4")
        self.lbl_status.grid(row=1, column=0, columnspan=2,
                              sticky="w", padx=20, pady=(0, 8))

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
        except Exception:
            tb = traceback.format_exc()
            messagebox.showerror("Ошибка расчёта", tb)
            self.lbl_status.configure(text="Ошибка расчёта.", text_color="#ef9a9a")

    def _on_clear(self):
        self._set_result("")
        self.lbl_status.configure(text="")

    def _set_result(self, text: str):
        self.txt_result.configure(state="normal")
        self.txt_result.delete("1.0", "end")
        self.txt_result.insert("1.0", text)
        self.txt_result.configure(state="disabled")

    def _show_results(self, params: dict, res: dict):
        lines = []
        sep   = "─" * 68

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

        lines.append("=" * 68)
        lines.append("  РАСЧЁТ МЕТАЛЛОЁМКОСТИ ПРОИЗВОДСТВЕННОГО ЗДАНИЯ")
        lines.append(f"  Шаг колонн: {params['col_step']} м  |  "
                     f"Пролёт фермы: {params['L_span']} м  |  "
                     f"Тип фермы: {params['truss_type']}")
        lines.append(f"  Кран: {params['q_crane_t']} т  |  "
                     f"Кранов: {params['n_cranes']}  |  "
                     f"{'С проходом' if params['with_pass'] else 'Без прохода'}")
        lines.append("=" * 68)

        h("ГЕОМЕТРИЯ")
        row("Длина здания, м:", params["L_build"])
        row("Ширина здания, м:", params["W_build"])
        row("Площадь пола, м²:", params["L_build"] * params["W_build"])
        row("Высота здания (ориент.), м:", f"~{round(params['h_rail'] + 1.5, 1)} (уточн. в логе)")

        h("1. ПРОГОНЫ  [Метод 1]")
        pr = res["прогоны"]
        row("Расчётная нагрузка, т/м:", pr["нагрузка_тм"])
        row("Подобранный профиль:", pr["профиль"])
        row("Масса 1 прогона, кг:", pr["масса_1шт_кг"])
        row("Количество в 1 шаге ферм:", pr["n_в_шаге"])
        row("Расход, кг/м²:", pr["расход_кгм2"])
        row("Масса ИТОГО, т:", pr["масса_общая_т"])

        h("2. СТРОПИЛЬНЫЕ ФЕРМЫ  [М1 + М2]")
        fm = res["фермы"]
        row("Нагрузка на ферму, т/м:", fm["нагрузка_тм"])
        row2("Расход, кг/м²:", fm["М1_расход_кгм2"], fm["М2_расход_кгм2"])
        row2("Масса ИТОГО, т:", fm["масса_общая_т_М1"], fm["масса_общая_т_М2"])

        h("3. СВЯЗИ ПОКРЫТИЯ  [Метод 2]")
        sv = res["связи_покрытия"]
        row("Расход, кг/м²:", sv["расход_кгм2"])
        row("Масса ИТОГО, т:", sv["масса_общая_т"])

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

        h("7. ФАХВЕРК  [Метод 2]")
        fh = res.get("фахверк", {})
        if "ошибка" in fh:
            row("Ошибка:", fh["ошибка"])
        else:
            row("Расход, кг/м² площади стен:", fh.get("расход_кгм2_стены", "н/п"))
            row("Площадь стен, м²:", fh.get("площадь_стен_м2", "н/п"))
            row("Масса ИТОГО, т:", fh.get("масса_общая_т", "н/п"))

        h("8. ОГРАЖДАЮЩИЕ КОНСТРУКЦИИ (справочно)")
        og = res["ограждение"]
        row("Площадь стен (периметр × высота), м²:", og["стены_м2"])
        row("Площадь кровли (длина × ширина), м²:",  og["кровля_м2"])

        h("9. ОПОРЫ ТРУБОПРОВОДОВ  [Метод 2]")
        op = res.get("опоры_трубопроводов", {})
        if "примечание" in op:
            row(op["примечание"])
        else:
            row("Расход, кг/м²:", op.get("расход_кгм2", "н/п"))
            row("Масса ИТОГО, т:", op.get("масса_общая_т", "н/п"))

        lines.append("\n" + "=" * 68)
        lines.append("  ИТОГО ПО КАРКАСУ")
        lines.append("=" * 68)
        it = res["итого"]
        lines.append(f"  {'Метод 1 (формулы):':<44}  {it['каркас_М1_т']} т  "
                     f"({it['каркас_М1_кгм2']} кг/м²)")
        lines.append(f"  {'Метод 2 (таблицы):':<44}  {it['каркас_М2_т']} т  "
                     f"({it['каркас_М2_кгм2']} кг/м²)")
        lines.append("=" * 68)

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
