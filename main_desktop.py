#!/usr/bin/env python3
"""
Металлоёмкость производственных зданий — десктопная версия v3.0
Поддержка: многопролётные здания, per-span параметры, режимы кранов,
           коррекция высоты колонн, гибридное суммирование.
БЭКАП v2.0 → main_desktop_backup_v2.py
"""
import math
import traceback
import datetime
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog

# ─────────────────────────────────────────────────────────
#  ТАБЛИЦЫ ДАННЫХ
# ─────────────────────────────────────────────────────────

PURLIN_TABLE = [
    (0.45, 110.4,  220.8, "Швеллер 20"),
    (0.65, 126.0,  252.0, "Швеллер 22"),
    (0.90, 144.0,  288.0, "Швеллер 24"),
    (1.25, 166.2,  332.4, "Швеллер 27"),
    (1.70, 190.8,  381.6, "Швеллер 30"),
    (2.50, 220.8,  441.6, "2×Швеллер 20"),
]

CRANE_BEAM_ALPHA = {
    5:0.08, 10:0.09, 20:0.12, 32:0.15, 50:0.18,
    80:0.22, 100:0.26, 125:0.30, 200:0.36, 320:0.40, 400:0.45,
}
RAIL_WEIGHT_KN = {
    5:0.461, 10:0.461, 20:0.461, 32:0.598, 50:0.598,
    80:0.831, 100:1.135, 125:1.135, 200:1.135, 320:1.417, 400:1.417,
}
BEAM_HEIGHT_RATIO = {
    20:(1/7,1/9), 32:(1/7,1/9), 50:(1/6,1/8.5),
    80:(1/6,1/7.5), 100:(1/6,1/7), 125:(1/6,1/7),
    160:(1/6,1/7), 200:(1/6,1/7),
}
CRANE_Q_EQUIV = {
    5:8, 10:12, 20:20, 32:28, 50:38, 80:55,
    100:68, 125:80, 200:105, 320:145, 400:175,
}

TRUSS_LOADS = [
    2.0,2.5,3.0,3.5,4.0,4.5,5.0,5.5,6.0,
    6.5,7.0,7.5,8.0,8.5,9.0,9.5,10.0,10.5,
    11.0,11.5,12.0,12.5,
]
TRUSS_MASSES = {
    "Уголки": {
        36:[5.90,7.54,10.37,11.12,12.30,12.74,13.30,14.74,15.66,15.66,18.89,18.89,18.89,19.30,21.50,21.50,22.52,23.70,24.57,24.57,26.30,26.92],
        30:[5.20,5.97,6.47,7.14,7.14,7.70,9.00,9.00,10.20,10.20,10.53,11.64,13.63,13.63,14.43,14.43,15.25,15.25,16.43,16.43,16.43,17.27],
        24:[2.30,3.16,3.94,3.97,4.29,5.75,5.75,6.28,6.28,6.28,6.53,6.53,6.90,7.97,8.87,8.87,8.87,8.87,8.87,9.11,10.45,11.24],
        18:[2.16,2.16,2.34,2.45,2.68,2.68,2.83,2.91,3.17,3.64,3.64,3.77,3.95,3.95,4.10,4.10,4.51,4.51,4.51,5.26,5.26,5.26],
    },
    "Двутавры": {
        36:[9.60,10.20,10.20,11.47,12.50,13.49,15.14,15.28,15.87,17.18,18.72,21.06,21.06,21.06,22.11,22.11,25.52,25.52,30.78,31.66,31.66,31.85],
        30:[6.27,6.38,6.38,8.07,8.23,8.90,9.84,9.93,10.35,12.99,12.99,12.99,12.99,14.89,14.89,14.89,15.35,18.68,18.68,18.68,19.69,19.69],
        24:[4.60,4.60,5.19,5.30,5.79,5.79,6.35,6.63,7.48,8.31,8.31,8.47,8.47,8.63,9.30,9.30,11.08,11.08,11.08,11.08,11.08,12.10],
        18:[2.92,2.92,2.92,2.92,3.37,3.92,3.92,3.92,4.34,4.34,4.34,4.72,4.72,4.72,4.72,4.72,5.42,5.42,5.49,5.49,5.86,5.86],
    },
    "Молодечно": {
        36:[7.00,8.05,9.20,12.25,13.53,13.53,15.96,17.18,17.61,21.26,21.26,23.01,24.25,29.80,29.80,29.80,29.80,29.80,31.57,37.40,37.40,37.40],
        30:[5.24,5.80,5.80,7.34,7.34,11.55,10.40,11.97,11.97,13.59,13.59,13.59,15.40,16.22,17.70,19.54,19.54,19.54,21.37,21.37,21.37,21.37],
        24:[2.48,3.60,3.85,4.11,5.07,5.07,6.18,6.24,6.47,8.02,8.02,8.70,9.37,9.37,10.00,10.90,10.90,11.54,11.54,12.37,13.62,13.62],
        18:[1.29,1.54,1.58,2.07,2.18,2.65,3.40,3.40,3.40,3.40,4.08,4.08,4.08,4.70,4.83,4.83,5.70,6.07,6.07,6.07,6.07,7.08],
    },
}

SUBTRUSS_LOADS  = [18.0,36.0,54.0,72.0,81.0,108.0,126.0,144.0,162.0,180.0,198.0,216.0,234.0,255.0]
SUBTRUSS_MASSES = [1.57,2.22,2.31,2.72,2.72,4.59,5.32,5.32,5.70,5.80,6.30,6.30,6.53,6.71]

FAKHVERK_DATA = {
    ('I',0,0):9,  ('I',0,1):10, ('I',0,2):11,
    ('I',1,0):9,  ('I',1,1):11, ('I',1,2):11,
    ('I',2,0):10, ('I',2,1):12, ('I',2,2):12,
    ('II',0,0):23,('II',0,1):25,('II',0,2):25,
    ('II',1,0):23,('II',1,1):25,('II',1,2):25,
    ('II',2,0):26,('II',2,1):30,('II',2,2):30,
    ('III',0,0):19,('III',0,1):28,('III',0,2):45,
    ('III',1,0):19,('III',1,1):29,('III',1,2):46,
    ('III',2,0):20,('III',2,1):30,('III',2,2):48,
}

_CB_Q1 = [5,10,20,32,50]
_CB_Q2 = [80,100,125,200,400]
CRANE_BEAM_T1 = {
    6:  [80,85,90,190,200,100,240,250,105,140],
    12: [150,160,320,350,180,200,390,440,220,470],
}
CRANE_BEAM_T2 = {
    12: [290,320,380,940,980,300,330,500,350,540],
    18: [460,480,500,1020,1080,490,520,540,1120,1180],
    24: [680,720,780,1040,1120,820,920,1620,1840,880],
}
BRAKE_T1 = {
    (6,True,True):[100,110],(6,True,False):[65,70],
    (6,False,True):[120,140],(6,False,False):[70,75],
    (12,True,True):[100,120],(12,True,False):[65,70],
    (12,False,True):[100,120],(12,False,False):[70,75],
}
BRAKE_T2 = {
    (12,True,True):[120,140],(12,True,False):[80,100],
    (12,False,True):[140,160],(12,False,False):[60,80],
    (18,True,True):[120,140],(18,True,False):[80,100],
    (18,False,True):[140,160],(18,False,False):[80,100],
    (24,True,True):[220,240],(24,True,False):[140,160],
    (24,False,True):[220,240],(24,False,False):[140,160],
}

# ── П.2: Кровельный пирог ─────────────────────────────────
# Удельный вес слоёв кровли (кН/м²) — заглушки, уточнить цифры
ROOF_MATERIALS = {
    "Профнастил Н-75 (t=0.8мм)":           0.10,
    "Профнастил Н-60 (t=0.7мм)":           0.08,
    "Профнастил НС-35 (t=0.7мм)":          0.06,
    "Утеплитель минвата 200мм":             0.05,
    "Утеплитель минвата 150мм":             0.04,
    "Утеплитель PIR 150мм":                 0.03,
    "Пароизоляция (плёнка)":                0.01,
    "Гидроизол. мембрана однослойная":      0.02,
    "Битумный ковёр 2 слоя (рубероид)":    0.06,
    "Стяжка цементная 30мм":                0.60,
    "Сэндвич-панель кровельная 200мм":      0.15,
}

# ── П.4: Коэффициент режима работы кранов ─────────────────
CRANE_MODE_FACTOR = {
    "Режим 1-6К":  1.00,   # лёгкий/средний режим
    "Режим 7-8К":  1.15,   # тяжёлый режим, доп. нагрузка +15%
}

# ─────────────────────────────────────────────────────────
#  ПОДСКАЗКИ ДЛЯ ПОЛЕЙ ВВОДА
# ─────────────────────────────────────────────────────────

TOOLTIPS = {
    'L_build':   "Длина здания по осям колонн, м.\nПринимается кратной шагу колонн.",
    'B_step':    "Шаг стропильных ферм B, м — расстояние между фермами вдоль здания.\nПринимается 6 или 12 м.",
    'col_step':  "Шаг колонн — расстояние между колоннами вдоль здания (6 или 12 м).\nПри шаге 12 м требуются подстропильные фермы.",
    'h_rail':    "Отметка головки рельса (УГР), м от ±0.000.\nОпределяется по технологическому заданию на кран.",
    'H_col_ov':  "Полная высота колонны, м. При 0 — вычисляется автоматически:\nH_кол = УГР + 4.5 м.",
    'Q_snow':    "Нормативная снеговая нагрузка, кН/м² (СП 20.13330.2017, Прил. Ж).\nРайоны: I — 0.8, II — 1.2, III — 1.8, IV — 2.4 кН/м².",
    'Q_dust':    "Нагрузка от технологической пыли на покрытие, кН/м².\nПринимается по технологическому заданию (0–1.0 кН/м²).",
    'Q_tech':    "Технологическая нагрузка (промышленные проводки и оборудование на кровле), кН/м².",
    'Q_roof':    "Нагрузка от кровельного покрытия (профнастил, утеплитель, мембрана и т.п.), кН/м².\nТипично: 0.15–0.50 кН/м².",
    'Q_purlin':  "Нормативная нагрузка от прогонов, кН/м².\nТипично: 0.15–0.35 кН/м².",
    'yc':        "Коэффициент надёжности по ответственности γn (ГОСТ 27751):\n• 1.0 — нормальный уровень ответственности\n• 1.1 — повышенный уровень\n• 1.2 — высший уровень",
    'rig_load':  "Нагрузка на ригель фахверка от стеновых панелей, кг/м.п.\nОпределяется по весу стеновых конструкций.",
    'bld_type':  "Тип здания — для расчёта металлоёмкости опор трубопроводов:\n• Основные производственные — 11–22 кг/м²\n• Здания энергоносителей — 23–40 кг/м²\n• Вспомогательные — 2–4 кг/м²",
    'L_span':    "Пролёт поперечной рамы L, м — расстояние между осями рядов колонн.\nСтандартные значения: 18, 24, 30, 36 м (ГОСТ 23837).",
    'truss_type':"Тип стропильных ферм:\n• Уголки — расчёт по Методу 1 (эмпирические формулы)\n• Двутавры / Молодечно — расчёт по Методу 2 (таблицы завода)",
    'q_crane':   "Грузоподъёмность мостового крана Q, т.\nВлияет на подкрановые балки, тормозные конструкции и колонны.",
    'n_cranes':  "Количество мостовых кранов в пролёте (1 или 2).\nПри 2 кранах нагрузка на подкрановые конструкции возрастает.",
    'with_pass': "Тип тормозных конструкций:\n• С проходом — тормозная балка с настилом для обслуживания\n• Без прохода — решётчатая тормозная конструкция (легче)",
    'crane_mode':"Режим работы крана по ГОСТ 25546:\n• Режим 1-6К — лёгкий и средний режим (αпб меньше)\n• Режим 7-8К — тяжёлый режим (αпб больше, конструкции тяжелее)",
    'has_post':  "Стойка фахверка при шаге 12м — промежуточная стойка фахверка.\nПри наличии — тип фахверка III (более тяжёлый).",
}


# ─────────────────────────────────────────────────────────
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ─────────────────────────────────────────────────────────

def _lkp(d, val):
    """Поиск с округлением вверх по sorted dict."""
    for k in sorted(d):
        if val <= k: return d[k]
    return d[sorted(d)[-1]]


def select_purlin(load_tm, span_m):
    for max_l, m6, m12, name in PURLIN_TABLE:
        if load_tm <= max_l:
            return (m6 if span_m <= 6 else m12), name
    _, m6, m12, name = PURLIN_TABLE[-1]
    return (m6 if span_m <= 6 else m12), f"{name}(!)"


def interp_table(loads, masses, target):
    for i, ld in enumerate(loads):
        if target <= ld: return masses[i]
    return masses[-1]


def ceil_to_table(target, values):
    for v in sorted(values):
        if target <= v: return v
    return sorted(values)[-1]


def get_truss_mass_m2(truss_type, span_m, load_tm):
    spans = sorted(TRUSS_MASSES.get(truss_type, {}).keys())
    if not spans: return None
    sk = ceil_to_table(span_m, spans)
    ms = TRUSS_MASSES[truss_type].get(sk)
    if ms is None: return None
    return interp_table(TRUSS_LOADS, ms, load_tm)


def get_subtruss_mass_m2(R_t):
    Rc = ceil_to_table(R_t, SUBTRUSS_LOADS)
    return interp_table(SUBTRUSS_LOADS, SUBTRUSS_MASSES, Rc)


def get_bracing_kgm2(q_crane_t, step_farm_m):
    if q_crane_t <= 120: return 15.0 if step_farm_m <= 6 else 35.0
    return 40.0 if step_farm_m <= 6 else 55.0


def get_crane_beam_kgm(q_crane_t, span_pb_m, n_cranes):
    try:
        table = CRANE_BEAM_T1 if q_crane_t <= 50 else CRANE_BEAM_T2
        q_ord = _CB_Q1 if q_crane_t <= 50 else _CB_Q2
        sk = ceil_to_table(span_pb_m, sorted(table.keys()))
        vals = table.get(sk)
        if vals is None: return None
        qi = min(range(len(q_ord)), key=lambda i: abs(q_ord[i]-q_crane_t))
        ci = qi*2 + (0 if n_cranes == 1 else 1)
        return vals[ci] if ci < len(vals) else None
    except: return None


def get_brake_kgm(q_crane_t, span_pb_m, n_cranes, with_passage, is_edge):
    try:
        table = BRAKE_T1 if q_crane_t <= 50 else BRAKE_T2
        sk = ceil_to_table(span_pb_m, sorted({k[0] for k in table}))
        vals = table.get((sk, is_edge, with_passage))
        if vals is None:
            for k, v in table.items():
                if k[0] == sk: vals = v; break
        if vals:
            return vals[0 if n_cranes == 1 else min(1, len(vals)-1)]
    except: pass
    return None


def get_fakhverk_kgm2(step_col_m, has_post, h_bld, rig_load):
    try:
        if step_col_m <= 6 and has_post: ft = 'III'
        elif step_col_m <= 6: ft = 'I'
        else: ft = 'II'
        lc = 0 if rig_load <= 0 else (1 if rig_load <= 100 else 2)
        hc = 0 if h_bld <= 10 else (1 if h_bld <= 20 else 2)
        return FAKHVERK_DATA.get((ft, lc, hc))
    except: return None


def get_pipe_support_kgm2(bld_type):
    d = {
        "Основные производственные": (11, 22),
        "Здания энергоносителей":     (23, 40),
        "Вспомогательные здания":     (2, 4),
    }
    lo, hi = d.get(bld_type, (11, 22))
    return (lo + hi) / 2


# ─────────────────────────────────────────────────────────
#  ОСНОВНОЙ РАСЧЁТ — многопролётная версия v3.0
# ─────────────────────────────────────────────────────────

def calculate(gp: dict, spans: list) -> dict:
    """
    gp   — глобальные параметры здания: L_build, Q_snow, Q_dust, Q_tech, yc
    spans — список пролётов, каждый содержит все per-span параметры:
            L_span, B_step, col_step, h_rail, H_col_ov,
            Q_roof, Q_purlin, truss_type, q_crane_t, n_cranes,
            with_pass, crane_mode, rig_load, has_post, bld_type
    Колонны: N пролётов → N+1 рядов колонн.
    Крайние ряды (2 шт.) — несут нагрузку от 1 пролёта.
    Средние ряды (N-1 шт.) — от 2 соседних пролётов.
    """
    res = {}
    log = []

    L_build = gp["L_build"]
    Q_snow  = gp["Q_snow"]
    Q_dust  = gp["Q_dust"]
    Q_tech  = gp["Q_tech"]
    yc      = gp["yc"]

    N = len(spans)
    W_build = sum(sp["L_span"] for sp in spans)
    S_floor = L_build * W_build
    P_walls = 2 * (L_build + W_build)

    log.append(f"Пролётов: {N}  W={W_build:.0f}м  S_пола={S_floor:.0f}м²")

    # ── Высота колонн — per-span ────────────────────────
    def _span_col_heights(sp):
        h_b = sp["col_step"] / 6 if sp["q_crane_t"] <= 50 else sp["col_step"] / 7
        if sp["q_crane_t"] <= 20:   h_r = 0.130
        elif sp["q_crane_t"] <= 50: h_r = 0.150
        elif sp["q_crane_t"] <= 80: h_r = 0.170
        else:                        h_r = 0.180
        H_full = sp["h_rail"] + 4.5
        if sp.get("H_col_ov", 0) > 0:
            H_full = sp["H_col_ov"]
        H_lower = sp["h_rail"] - h_b - h_r + 0.6
        H_upper = H_full - H_lower
        return H_upper, H_lower, H_full

    span_heights = [_span_col_heights(sp) for sp in spans]

    for i, (H_upper, H_lower, H_full) in enumerate(span_heights):
        log.append(f"Пролёт {i+1}: H_кол={H_full:.2f}м (надкр={H_upper:.2f}м  подкр={H_lower:.2f}м)")

    # Для ограждения и фахверка берём max H_full
    H_full_max = max(h[2] for h in span_heights)
    S_walls = P_walls * H_full_max

    # ── 1+2. Прогоны и фермы — по пролётам ─────────────
    g_links = 0.05

    G_pur_all_t = 0.0
    G_tr_m1_all = 0.0
    G_tr_m2_all = 0.0
    span_data   = []

    for i, sp in enumerate(spans):
        L  = sp["L_span"]
        tt = sp["truss_type"]
        B  = sp["B_step"]
        Ss = L_build * L

        # Per-span нагрузки
        Q_load_total = sp["Q_roof"] + sp["Q_purlin"] + Q_snow + Q_dust + Q_tech + g_links
        gn_total     = Q_load_total

        # Прогоны
        a_pr = 3.0
        qp_tm = (sp["Q_roof"] + sp["Q_purlin"] + Q_snow + Q_dust + Q_tech) * a_pr * yc / 9.81
        mp, pname = select_purlin(qp_tm, B)
        n_pr = int(L / a_pr) + 1
        g_pur = mp * n_pr / (L * B)
        G_pur_t = g_pur * Ss / 1000
        G_pur_all_t += G_pur_t

        # Фермы — нагрузка
        n_tr = L_build / B + 1
        Q_tm = gn_total * B * yc / 9.81

        # М1 (только Уголки)
        G_tr1 = None
        if tt == "Уголки":
            Gkn  = (gn_total * B / 1000 + 0.018) * 1.4 * L**2 / 0.85 * yc
            G_tr1 = Gkn / 9.81 * n_tr
            G_tr_m1_all += G_tr1

        # М2 (таблица)
        G_tr2 = None
        mt = get_truss_mass_m2(tt, L, Q_tm)
        if mt is not None:
            G_tr2 = mt * n_tr
            G_tr_m2_all += G_tr2

        span_data.append({
            "idx": i+1, "L_span": L, "S_span": Ss, "tt": tt,
            "B_step": B,
            "purlin": pname, "qp_tm": round(qp_tm, 3),
            "g_pur_kgm2": round(g_pur, 2), "G_pur_t": round(G_pur_t, 2),
            "Q_tm": round(Q_tm, 3),
            "G_tr_m1": round(G_tr1, 2) if G_tr1 is not None else "н/п",
            "G_tr_m2": round(G_tr2, 2) if G_tr2 is not None else "н/п",
            "Q_load_total": Q_load_total,
        })

    res["прогоны"] = {
        "масса_общая_т": round(G_pur_all_t, 2),
        "по_пролётам": [{"пролёт":d["idx"],"профиль":d["purlin"],
            "нагрузка_тм":d["qp_tm"],"расход_кгм2":d["g_pur_kgm2"],
            "масса_т":d["G_pur_t"]} for d in span_data],
    }
    res["фермы"] = {
        "масса_общая_т_М1": round(G_tr_m1_all, 2),
        "масса_общая_т_М2": round(G_tr_m2_all, 2),
        "по_пролётам": [{"пролёт":d["idx"],"нагрузка_тм":d["Q_tm"],
            "G_М1_т":d["G_tr_m1"],"G_М2_т":d["G_tr_m2"]} for d in span_data],
    }

    # ── 3. Связи покрытия — per-span, суммарно ──────────
    G_br_total = 0.0
    br_rows = []
    for i, sp in enumerate(spans):
        Ss = L_build * sp["L_span"]
        g_br_sp = get_bracing_kgm2(sp["q_crane_t"], sp["B_step"])
        G_br_sp = g_br_sp * Ss / 1000
        G_br_total += G_br_sp
        br_rows.append({"пролёт": i+1, "расход_кгм2": g_br_sp, "масса_т": round(G_br_sp, 2)})

    res["связи_покрытия"] = {
        "расход_кгм2": round(G_br_total * 1000 / S_floor, 2) if S_floor else 0,
        "масса_общая_т": round(G_br_total, 2),
        "по_пролётам": br_rows,
    }

    # ── 4. Подстропильные фермы — per-span ───────────────
    G_sub_m1 = 0.0
    G_sub_m2 = 0.0
    sub_rows = []
    need_sub = any(sp["col_step"] == 12 and sp["B_step"] < sp["col_step"] for sp in spans)
    if need_sub:
        for i, sp in enumerate(spans):
            if not (sp["col_step"] == 12 and sp["B_step"] < sp["col_step"]):
                sub_rows.append({"пролёт": i+1, "G_М1_т": 0, "G_М2_т": "н/п", "R_кн": 0})
                continue
            L = sp["L_span"]
            B = sp["B_step"]
            Q_load_sp = span_data[i]["Q_load_total"]
            gn_sp = Q_load_sp
            n_bays = L_build / sp["col_step"]
            Q_tm_sp = gn_sp * B * yc / 9.81
            R_kn = gn_sp * B * yc * L / 2
            R_t  = R_kn / 9.81
            Rf   = max(100, min(R_kn, 400))
            apf  = (Rf - 100) * 0.0002 + 0.044
            G1   = apf * 144 * n_bays / N
            G_sub_m1 += G1
            mt = get_subtruss_mass_m2(R_t)
            G2 = mt * n_bays / N if mt else None
            if G2: G_sub_m2 += G2
            sub_rows.append({"пролёт": i+1, "R_кн": round(R_kn, 1),
                "G_М1_т": round(G1, 2), "G_М2_т": round(G2, 2) if G2 else "н/п"})
        res["подстропильные_фермы"] = {
            "масса_общая_т_М1": round(G_sub_m1, 2),
            "масса_общая_т_М2": round(G_sub_m2, 2),
            "по_пролётам": sub_rows,
        }
    else:
        res["подстропильные_фермы"] = {"примечание": "Не требуются"}

    # ── 5. Подкрановые балки — по рядам колонн ──────────
    # Для каждого ряда используем col_step соответствующего пролёта
    G_pb_m1 = 0.0
    G_pb_m2 = 0.0
    pb_rows = []

    def _pb_row(sp_obj, is_edge, label):
        nonlocal G_pb_m1, G_pb_m2
        q  = sp_obj["q_crane_t"]
        nc = sp_obj["n_cranes"]
        wp = sp_obj["with_pass"]
        mf = CRANE_MODE_FACTOR[sp_obj["crane_mode"]]
        L_pb_loc = float(sp_obj["col_step"])
        n_bays_a = math.ceil(L_build / L_pb_loc)
        alp = _lkp(CRANE_BEAM_ALPHA, q)
        qr  = _lkp(RAIL_WEIGHT_KN, q)
        G1t = (alp * L_pb_loc + qr) * L_pb_loc * 1.4 / 9.81
        G_pb_m1 += G1t * n_bays_a
        pb_kgm = get_crane_beam_kgm(q, L_pb_loc, nc)
        br_kgm = get_brake_kgm(q, L_pb_loc, nc, wp, is_edge)
        if pb_kgm and br_kgm is not None:
            G_pb_m2 += (pb_kgm * mf + br_kgm * mf) * L_pb_loc * n_bays_a / 1000
        pb_rows.append({"ряд": label, "G_М1_т": round(G1t * n_bays_a, 2), "q": q})

    # Крайний левый (пролёт 0)
    _pb_row(spans[0], True, "Крайний Л")
    # Средние
    for mi in range(1, N):
        _pb_row(spans[mi-1], False, f"Средний {mi} (лев)")
        _pb_row(spans[mi],   False, f"Средний {mi} (прав)")
    # Крайний правый
    _pb_row(spans[N-1], True, "Крайний П")

    res["подкрановые_балки"] = {
        "масса_общая_т_М1": round(G_pb_m1, 2),
        "масса_общая_т_М2": round(G_pb_m2, 2) if G_pb_m2 > 0 else "н/п",
        "ряды_колонн": pb_rows,
    }

    # ── 6. Колонны — с учётом топологии и per-span высот ─
    rho=78.5; pu=1.4; pl=2.1; kMu=0.275; kMl=0.45
    gst=0.25; aw=0.15

    def _col_kg(L_sp, q_cr, H_up, H_lo, cs, Q_load_sp):
        L_pb_loc = float(cs)
        Gwu = gst * H_up * (1 - aw) * cs
        Gwl = gst * H_lo * (1 - aw) * cs
        SFv = Q_load_sp * cs * L_sp / 2 + Gwu
        Gcu = SFv * rho * pu * H_up / (kMu * 24000)
        qeq = _lkp(CRANE_Q_EQUIV, q_cr)
        D   = qeq * cs * 1.1 * yc
        alp = _lkp(CRANE_BEAM_ALPHA, q_cr)
        qrr = _lkp(RAIL_WEIGHT_KN, q_cr)
        Gpb = (alp * L_pb_loc + qrr) * L_pb_loc * 1.4
        SFn = SFv + D + Gpb + Gwl + Gcu
        Gcl = SFn * rho * pl * H_lo / (kMl * 24000)
        return (Gcu + Gcl) / 9.81 * 1000

    G_cols_t = 0.0
    col_rows_detail = []

    # Крайний левый ряд — пролёт 0
    sp0 = spans[0]
    H_up0, H_lo0, H_full0 = span_heights[0]
    n_col_along_0 = round(L_build / sp0["col_step"]) + 1
    Q_load_0 = span_data[0]["Q_load_total"]
    Gce = _col_kg(sp0["L_span"], sp0["q_crane_t"], H_up0, H_lo0, sp0["col_step"], Q_load_0)
    G_cols_t += Gce * n_col_along_0 / 1000
    col_rows_detail.append({
        "ряд": "Крайний Л",
        "масса_1_кг": round(Gce, 1),
        "масса_ряд_т": round(Gce * n_col_along_0 / 1000, 2),
    })

    # Средние ряды — используем параметры левого пролёта
    for mi in range(1, N):
        sL = spans[mi-1]
        sR = spans[mi]
        H_upL, H_loL, H_fullL = span_heights[mi-1]
        cs_mid = sL["col_step"]
        n_col_mid = round(L_build / cs_mid) + 1
        Q_load_L = span_data[mi-1]["Q_load_total"]
        Q_load_R = span_data[mi]["Q_load_total"]
        Gwu = gst * H_upL * (1 - aw) * cs_mid
        Gwl = gst * H_loL * (1 - aw) * cs_mid
        SFv = (Q_load_L + Q_load_R) * cs_mid * (sL["L_span"] + sR["L_span"]) / 4 + Gwu
        Gcu = SFv * rho * pu * H_upL / (kMu * 24000)
        qeqL = _lkp(CRANE_Q_EQUIV, sL["q_crane_t"])
        qeqR = _lkp(CRANE_Q_EQUIV, sR["q_crane_t"])
        D = (qeqL + qeqR) * cs_mid * 1.1 * yc
        alpL = _lkp(CRANE_BEAM_ALPHA, sL["q_crane_t"])
        qrL  = _lkp(RAIL_WEIGHT_KN,  sL["q_crane_t"])
        alpR = _lkp(CRANE_BEAM_ALPHA, sR["q_crane_t"])
        qrR  = _lkp(RAIL_WEIGHT_KN,  sR["q_crane_t"])
        L_pb_L = float(sL["col_step"])
        L_pb_R = float(sR["col_step"])
        Gpb = (alpL * L_pb_L + qrL) * L_pb_L * 1.4 + (alpR * L_pb_R + qrR) * L_pb_R * 1.4
        SFn = SFv + D + Gpb + Gwl + Gcu
        Gcl = SFn * rho * pl * H_loL / (kMl * 24000)
        Gcm_kg = (Gcu + Gcl) / 9.81 * 1000
        G_cols_t += Gcm_kg * n_col_mid / 1000
        col_rows_detail.append({
            "ряд": f"Средний {mi}",
            "масса_1_кг": round(Gcm_kg, 1),
            "масса_ряд_т": round(Gcm_kg * n_col_mid / 1000, 2),
        })

    # Крайний правый ряд — пролёт N-1
    spN = spans[N-1]
    H_upN, H_loN, H_fullN = span_heights[N-1]
    n_col_along_N = round(L_build / spN["col_step"]) + 1
    Q_load_N = span_data[N-1]["Q_load_total"]
    Gce2 = _col_kg(spN["L_span"], spN["q_crane_t"], H_upN, H_loN, spN["col_step"], Q_load_N)
    G_cols_t += Gce2 * n_col_along_N / 1000
    col_rows_detail.append({
        "ряд": "Крайний П",
        "масса_1_кг": round(Gce2, 1),
        "масса_ряд_т": round(Gce2 * n_col_along_N / 1000, 2),
    })

    n_col_total = n_col_along_0 * (N + 1)

    # Для отображения — первый пролёт
    H_full_disp  = span_heights[0][2]
    H_upper_disp = span_heights[0][0]
    H_lower_disp = span_heights[0][1]

    # Сохраним все высоты по пролётам для отображения
    span_heights_list = [
        {"пролёт": i+1, "H_full": round(h[2], 2),
         "H_upper": round(h[0], 2), "H_lower": round(h[1], 2)}
        for i, h in enumerate(span_heights)
    ]

    res["колонны"] = {
        "n_колонн": n_col_total,
        "H_full_м":  round(H_full_disp, 2),
        "H_upper_м": round(H_upper_disp, 2),
        "H_lower_м": round(H_lower_disp, 2),
        "высоты_пролётов": span_heights_list,
        "расход_кгм2": round(G_cols_t * 1000 / S_floor, 2) if S_floor else 0,
        "масса_общая_т": round(G_cols_t, 2),
        "по_рядам": col_rows_detail,
    }

    # ── 7. Фахверк — per-span ──────────────────────────
    G_fakh_total = 0.0
    fakh_rows = []
    for i, sp in enumerate(spans):
        H_full_sp = span_heights[i][2]
        # Площадь стен, приходящаяся на данный пролёт (пропорционально)
        S_walls_sp = P_walls * H_full_sp / N
        gf = get_fakhverk_kgm2(sp["col_step"], sp["has_post"], H_full_sp, sp["rig_load"])
        if gf:
            G_fakh_sp = gf * S_walls_sp / 1000
            G_fakh_total += G_fakh_sp
            fakh_rows.append({"пролёт": i+1, "расход_кгм2_стены": gf,
                               "масса_т": round(G_fakh_sp, 2)})
        else:
            fakh_rows.append({"пролёт": i+1, "ошибка": "Не определён", "масса_т": 0})

    if G_fakh_total > 0:
        res["фахверк"] = {
            "расход_кгм2_стены": round(G_fakh_total * 1000 / S_walls, 2) if S_walls else 0,
            "площадь_стен_м2": round(S_walls, 1),
            "масса_общая_т": round(G_fakh_total, 2),
            "по_пролётам": fakh_rows,
        }
    else:
        res["фахверк"] = {"ошибка": "Не определён", "масса_общая_т": 0,
                          "по_пролётам": fakh_rows}

    # ── 8. Ограждение ───────────────────────────────────
    res["ограждение"] = {"стены_м2": round(S_walls, 1), "кровля_м2": round(S_floor, 1)}

    # ── 9. Опоры трубопроводов — per-span ───────────────
    G_pipe_total = 0.0
    pipe_rows = []
    for i, sp in enumerate(spans):
        Ss = L_build * sp["L_span"]
        gp2 = get_pipe_support_kgm2(sp["bld_type"])
        G_pipe_sp = gp2 * Ss / 1000
        G_pipe_total += G_pipe_sp
        pipe_rows.append({"пролёт": i+1, "расход_кгм2": gp2, "масса_т": round(G_pipe_sp, 2)})

    res["опоры_трубопроводов"] = {
        "расход_кгм2": round(G_pipe_total * 1000 / S_floor, 2) if S_floor else 0,
        "масса_общая_т": round(G_pipe_total, 2),
        "по_пролётам": pipe_rows,
    }

    # ── П.6: Гибридное суммирование ─────────────────────
    def sv(d, *keys):
        for k in keys:
            v = d.get(k)
            if isinstance(v, (int, float)): return float(v)
        return 0.0

    common = (
        sv(res["прогоны"],               "масса_общая_т")
        + sv(res["колонны"],             "масса_общая_т")
        + sv(res["связи_покрытия"],      "масса_общая_т")
        + sv(res["фахверк"],             "масса_общая_т")
        + sv(res["опоры_трубопроводов"], "масса_общая_т")
    )

    m1_spec = (
        sv(res["фермы"],                  "масса_общая_т_М1")
        + sv(res["подстропильные_фермы"], "масса_общая_т_М1")
        + sv(res["подкрановые_балки"],    "масса_общая_т_М1")
    )

    m2_spec = (
        sv(res["фермы"],                  "масса_общая_т_М2")
        + sv(res["подстропильные_фермы"], "масса_общая_т_М2")
        + sv(res["подкрановые_балки"],    "масса_общая_т_М2")
    )

    total_m1 = common + m1_spec
    total_m2 = common + m2_spec

    res["итого"] = {
        "М1_т":    round(total_m1, 2),
        "М2_т":    round(total_m2, 2),
        "М1_кгм2": round(total_m1 * 1000 / S_floor, 2) if S_floor else 0,
        "М2_кгм2": round(total_m2 * 1000 / S_floor, 2) if S_floor else 0,
        "min_т":   round(min(total_m1, total_m2), 2),
        "max_т":   round(max(total_m1, total_m2), 2),
        "S_floor": round(S_floor, 1),
    }
    res["_log"] = log
    return res


# ─────────────────────────────────────────────────────────
#  ВСПЛЫВАЮЩАЯ ПОДСКАЗКА
# ─────────────────────────────────────────────────────────

class ToolTip:
    """Всплывающая подсказка при наведении курсора на виджет (задержка 450 мс)."""

    def __init__(self, widget: tk.Widget, text: str):
        self._widget = widget
        self._text = text
        self._tip = None
        self._after_id = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._cancel, add="+")
        widget.bind("<ButtonPress>", self._cancel, add="+")

    def _schedule(self, _event=None):
        self._cancel()
        self._after_id = self._widget.after(450, self._show)

    def _cancel(self, _event=None):
        if self._after_id:
            self._widget.after_cancel(self._after_id)
            self._after_id = None
        self._hide()

    def _show(self):
        if self._tip:
            return
        x = self._widget.winfo_rootx() + 28
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._tip = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        outer = tk.Frame(tw, background="#1c2340",
                         highlightbackground="#4a6fa5", highlightthickness=1)
        outer.pack()
        tk.Label(
            outer, text=self._text, justify="left",
            background="#1c2340", foreground="#c8dcff",
            wraplength=380, padx=10, pady=8,
            font=("", 10),
        ).pack()

    def _hide(self):
        if self._tip:
            self._tip.destroy()
            self._tip = None


# ─────────────────────────────────────────────────────────
#  GUI — customtkinter
# ─────────────────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FL  = ("Segoe UI", 12)
FT  = ("Segoe UI", 13, "bold")
FH  = ("Segoe UI", 11)
FRE = ("Consolas", 12)
PAD = {"padx": 6, "pady": 3}


class FloatEntry(ctk.CTkEntry):
    def get_float(self, default=0.0):
        try: return float(self.get().replace(",", "."))
        except: return default


class SpanFrame(ctk.CTkFrame):
    """Карточка одного пролёта — все per-span параметры."""

    def __init__(self, parent, span_num: int, on_remove):
        super().__init__(parent, fg_color="#1e2a3a", corner_radius=8)
        self._num = span_num
        self._on_remove = on_remove
        self._build(span_num)

    def _build(self, n):
        # Заголовок
        hdr = ctk.CTkFrame(self, fg_color="#243347", corner_radius=6)
        hdr.pack(fill="x", padx=6, pady=(6, 2))
        self._lbl = ctk.CTkLabel(hdr, text=f"  Пролёт {n}", font=FT,
                                  text_color="#4fc3f7")
        self._lbl.pack(side="left", padx=4, pady=4)
        ctk.CTkButton(hdr, text="✕ Удалить", font=FH, width=90, height=24,
                      fg_color="#b71c1c", hover_color="#7f0000",
                      command=lambda: self._on_remove(self)
                      ).pack(side="right", padx=4, pady=4)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="x", padx=8, pady=4)
        body.columnconfigure(1, weight=1)
        body.columnconfigure(2, weight=0)

        self._row = 0

        def sec(text):
            ctk.CTkLabel(body, text=text, font=FT, text_color="#4fc3f7",
                         anchor="w").grid(
                row=self._row, column=0, columnspan=3, sticky="w",
                padx=PAD["padx"], pady=(8, 2))
            self._row += 1

        def fe(lbl, default, tip_key=None):
            ctk.CTkLabel(body, text=lbl, font=FL, anchor="w").grid(
                row=self._row, column=0, sticky="w", **PAD)
            e = FloatEntry(body, width=110)
            e.insert(0, str(default))
            e.grid(row=self._row, column=1, sticky="w", **PAD)
            if tip_key and tip_key in TOOLTIPS:
                qb = ctk.CTkButton(
                    body, text="?", width=22, height=22,
                    fg_color="transparent", hover_color="#2a3a5a",
                    text_color="#5588cc", border_color="#3a5a8a", border_width=1,
                    font=FH, command=lambda: None, corner_radius=11,
                )
                qb.grid(row=self._row, column=2, sticky="w", padx=(2, 4), pady=PAD["pady"])
                ToolTip(qb, TOOLTIPS[tip_key])
            self._row += 1
            return e

        def cmb(lbl, values, default=None, tip_key=None):
            ctk.CTkLabel(body, text=lbl, font=FL, anchor="w").grid(
                row=self._row, column=0, sticky="w", **PAD)
            v = ctk.StringVar(value=default or values[0])
            c = ctk.CTkComboBox(body, values=values, variable=v, width=200)
            c.grid(row=self._row, column=1, sticky="w", **PAD)
            if tip_key and tip_key in TOOLTIPS:
                qb = ctk.CTkButton(
                    body, text="?", width=22, height=22,
                    fg_color="transparent", hover_color="#2a3a5a",
                    text_color="#5588cc", border_color="#3a5a8a", border_width=1,
                    font=FH, command=lambda: None, corner_radius=11,
                )
                qb.grid(row=self._row, column=2, sticky="w", padx=(2, 4), pady=PAD["pady"])
                ToolTip(qb, TOOLTIPS[tip_key])
            self._row += 1
            return v

        def chk(lbl, default=False, tip_key=None):
            var = ctk.BooleanVar(value=default)
            cb = ctk.CTkCheckBox(body, text=lbl, variable=var, font=FL)
            cb.grid(row=self._row, column=0, columnspan=2, sticky="w", **PAD)
            if tip_key and tip_key in TOOLTIPS:
                qb = ctk.CTkButton(
                    body, text="?", width=22, height=22,
                    fg_color="transparent", hover_color="#2a3a5a",
                    text_color="#5588cc", border_color="#3a5a8a", border_width=1,
                    font=FH, command=lambda: None, corner_radius=11,
                )
                qb.grid(row=self._row, column=2, sticky="w", padx=(2, 4), pady=PAD["pady"])
                ToolTip(qb, TOOLTIPS[tip_key])
            self._row += 1
            return var

        # ── Геометрия пролёта ──────────────────────────
        sec("Геометрия пролёта")
        self.e_L    = fe("Пролёт L, м",                          24,   'L_span')
        self.v_B    = cmb("Шаг ферм B, м",      ["6", "12"],     "6",  'B_step')
        self.v_col  = cmb("Шаг колонн, м",      ["6", "12"],     "12", 'col_step')
        self.e_rail = fe("Уровень рельса, м",                     10.0, 'h_rail')
        self.e_hov  = fe("Переопределить H_кол, м (0=авто)",      0,    'H_col_ov')

        # ── Кровля и прогоны ───────────────────────────
        sec("Кровля и прогоны")
        self.e_roof = fe("Нагрузка кровли, кН/м²",  0.30, 'Q_roof')
        self.e_pur  = fe("Вес прогонов, кН/м²",     0.35, 'Q_purlin')

        # ── Кран ───────────────────────────────────────
        sec("Кран")
        self.v_tt  = cmb("Тип фермы",
                         ["Уголки", "Двутавры", "Молодечно"],
                         tip_key='truss_type')
        self.e_q   = fe("Г/п крана, т",  50, 'q_crane')
        self.v_nc  = cmb("Кранов в пролёте", ["1", "2"])
        self.v_wp  = cmb("Тормозные пути",
                         ["С проходом", "Без прохода"],
                         tip_key='with_pass')
        self.v_cm  = cmb("Режим работы крана",
                         list(CRANE_MODE_FACTOR.keys()),
                         "Режим 1-6К",
                         tip_key='crane_mode')

        # ── Фахверк и тип здания ───────────────────────
        sec("Фахверк и тип здания")
        self.e_rig      = fe("Нагрузка на ригели, кг/м.п.", 0, 'rig_load')
        self.v_post_var = chk("Стойка фахверка (шаг 12м)", False, 'has_post')
        self.v_bld      = cmb("Тип здания",
                              ["Основные производственные",
                               "Здания энергоносителей",
                               "Вспомогательные здания"],
                              tip_key='bld_type')

    def update_title(self, n):
        self._num = n
        self._lbl.configure(text=f"  Пролёт {n}")

    def get_params(self) -> dict:
        return {
            "L_span":     self.e_L.get_float(24),
            "B_step":     float(self.v_B.get()),
            "col_step":   float(self.v_col.get()),
            "h_rail":     self.e_rail.get_float(10.0),
            "H_col_ov":   self.e_hov.get_float(0),
            "Q_roof":     self.e_roof.get_float(0.30),
            "Q_purlin":   self.e_pur.get_float(0.35),
            "truss_type": self.v_tt.get(),
            "q_crane_t":  self.e_q.get_float(50),
            "n_cranes":   int(self.v_nc.get()),
            "with_pass":  self.v_wp.get() == "С проходом",
            "crane_mode": self.v_cm.get(),
            "rig_load":   self.e_rig.get_float(0),
            "has_post":   self.v_post_var.get(),
            "bld_type":   self.v_bld.get(),
        }


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Металлоёмкость производственных зданий v3.0")
        self.geometry("1580x980")
        self.resizable(True, True)
        self._span_frames: list[SpanFrame] = []
        self._last_results_text = ""
        self._build_ui()

    # ── Построение интерфейса ────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # ─ Левая панель ─────────────────────────────────
        left = ctk.CTkScrollableFrame(self, label_text="Входные параметры", width=540)
        left.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        left.columnconfigure(1, weight=1)
        left.columnconfigure(2, weight=0)

        self._r = 0

        def sec(t):
            ctk.CTkLabel(left, text=t, font=FT, text_color="#4fc3f7").grid(
                row=self._r, column=0, columnspan=3, sticky="w", **PAD)
            self._r += 1

        def _qbtn(tip_key):
            if tip_key and tip_key in TOOLTIPS:
                qb = ctk.CTkButton(
                    left, text="?", width=22, height=22,
                    fg_color="transparent", hover_color="#2a3a5a",
                    text_color="#5588cc", border_color="#3a5a8a", border_width=1,
                    font=FH, command=lambda: None, corner_radius=11,
                )
                qb.grid(row=self._r - 1, column=2, sticky="w",
                        padx=(2, 4), pady=PAD["pady"])
                ToolTip(qb, TOOLTIPS[tip_key])

        def ent(lbl, default, tip_key=None):
            ctk.CTkLabel(left, text=lbl, font=FL, anchor="w").grid(
                row=self._r, column=0, sticky="w", **PAD)
            e = FloatEntry(left, width=120)
            e.insert(0, str(default))
            e.grid(row=self._r, column=1, sticky="w", **PAD)
            self._r += 1
            _qbtn(tip_key)
            return e

        # ── Геометрия здания ────────────────────────────
        sec("Геометрия здания")
        self.e_L_build = ent("Длина по осям, м", 120, 'L_build')

        # ── Нагрузки ───────────────────────────────────
        sec("Нагрузки (кН/м²)")
        self.e_Q_snow = ent("Снег Qснег",               2.1, 'Q_snow')
        self.e_Q_dust = ent("Пыль Qпыль",               0.0, 'Q_dust')
        self.e_Q_tech = ent("Технол. нагрузка, кН/м²",  0.0, 'Q_tech')

        # ── Общие параметры ─────────────────────────────
        sec("Общие параметры")
        self.e_yc = ent("Коэф. ответственности γc", 1.0, 'yc')

        # ── Кнопки ─────────────────────────────────────
        self._r += 1
        btn_fr = ctk.CTkFrame(left, fg_color="transparent")
        btn_fr.grid(row=self._r, column=0, columnspan=3, pady=8)
        ctk.CTkButton(btn_fr, text="  Рассчитать", font=FT, width=180, height=44,
                      fg_color="#1565c0", hover_color="#0d47a1",
                      command=self._on_calculate).pack(side="left", padx=5)
        ctk.CTkButton(btn_fr, text="Очистить", font=FL, width=100, height=44,
                      fg_color="#37474f", hover_color="#263238",
                      command=self._on_clear).pack(side="left", padx=5)
        self.btn_save = ctk.CTkButton(
            btn_fr, text="  Сохранить результаты", font=FL, width=200, height=44,
            fg_color="#1b5e20", hover_color="#2e7d32", state="disabled",
            command=self._save_results)
        self.btn_save.pack(side="left", padx=5)
        ToolTip(self.btn_save,
                "Сохранить результаты расчёта в текстовый файл (.txt).\nДоступно после нажатия «Рассчитать».")
        self._r += 1

        # ── Пролёты ────────────────────────────────────
        sec("─── Пролёты здания ───────────────────────────────")
        self._spans_container = ctk.CTkFrame(left, fg_color="transparent")
        self._spans_container.grid(row=self._r, column=0, columnspan=3, sticky="ew")
        self._r += 1

        add_btn_row = ctk.CTkFrame(left, fg_color="transparent")
        add_btn_row.grid(row=self._r, column=0, columnspan=3, pady=4)
        ctk.CTkButton(add_btn_row, text="＋ Добавить пролёт", font=FL,
                      fg_color="#1b5e20", hover_color="#2e7d32",
                      command=self._add_span).pack()
        self._r += 1

        # Добавить 1 пролёт по умолчанию
        self._add_span()

        # ─ Правая панель ────────────────────────────────
        right = ctk.CTkFrame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Результаты расчёта", font=FT
                     ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))
        self.txt = ctk.CTkTextbox(right, font=FRE, wrap="word", state="disabled")
        self.txt.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))

        self.lbl_status = ctk.CTkLabel(self, text="", font=FL, text_color="#80cbc4")
        self.lbl_status.grid(row=1, column=0, columnspan=2, sticky="w",
                              padx=20, pady=(0, 8))

    # ── Управление пролётами ─────────────────────────────

    def _add_span(self):
        n = len(self._span_frames) + 1
        sf = SpanFrame(self._spans_container, n, self._remove_span)
        sf.pack(fill="x", padx=4, pady=4)
        self._span_frames.append(sf)

    def _remove_span(self, sf: SpanFrame):
        if len(self._span_frames) <= 1:
            messagebox.showwarning("Внимание", "Должен быть хотя бы один пролёт.")
            return
        self._span_frames.remove(sf)
        sf.pack_forget()
        sf.destroy()
        for i, f in enumerate(self._span_frames):
            f.update_title(i + 1)

    # ── Параметры ────────────────────────────────────────

    def _read_global_params(self) -> dict:
        return {
            "L_build": self.e_L_build.get_float(120),
            "Q_snow":  self.e_Q_snow.get_float(2.1),
            "Q_dust":  self.e_Q_dust.get_float(0.0),
            "Q_tech":  self.e_Q_tech.get_float(0.0),
            "yc":      self.e_yc.get_float(1.0),
        }

    # ── Действия ─────────────────────────────────────────

    def _on_calculate(self):
        self.lbl_status.configure(text="Расчёт…", text_color="#ffcc80")
        self.update()
        try:
            gp    = self._read_global_params()
            spans = [sf.get_params() for sf in self._span_frames]
            if not spans:
                messagebox.showwarning("Нет пролётов", "Добавьте хотя бы один пролёт.")
                return
            res = calculate(gp, spans)
            self._show_results(gp, spans, res)
            self.lbl_status.configure(text="Расчёт завершён.", text_color="#80cbc4")
            self.btn_save.configure(state="normal")
        except Exception:
            tb = traceback.format_exc()
            messagebox.showerror("Ошибка расчёта", tb)
            self.lbl_status.configure(text="Ошибка.", text_color="#ef9a9a")

    def _on_clear(self):
        self._set_txt("")
        self._last_results_text = ""
        self.btn_save.configure(state="disabled")
        self.lbl_status.configure(text="")

    def _save_results(self):
        """Сохранение результатов расчёта в текстовый файл."""
        if not self._last_results_text:
            return
        now = datetime.datetime.now()
        default_name = f"metalloemkost_{now.strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".txt",
            filetypes=[("Текстовый файл", "*.txt"), ("Все файлы", "*.*")],
            initialfile=default_name,
            title="Сохранить результаты расчёта",
        )
        if not filepath:
            return
        try:
            header = (
                "РАСЧЁТ МЕТАЛЛОЁМКОСТИ ПРОИЗВОДСТВЕННЫХ ЗДАНИЙ С МОСТОВЫМИ КРАНАМИ\n"
                f"Дата расчёта: {now.strftime('%d.%m.%Y %H:%M:%S')}\n"
                + "=" * 70 + "\n\n"
            )
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(header)
                f.write(self._last_results_text)
            self.lbl_status.configure(
                text=f"Сохранено: {filepath}", text_color="#80cbc4")
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", str(e))

    def _set_txt(self, text: str):
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", text)
        self.txt.configure(state="disabled")

    # ── Вывод результатов ────────────────────────────────

    def _show_results(self, gp, spans, res):
        L = []
        S = "─" * 70

        def h(t):  L.append(f"\n{S}\n  {t}\n{S}")
        def rw(lbl, *vs): L.append(f"  {lbl:<44}  {'  '.join(str(v) for v in vs)}")
        def r2(lbl, m1, m2): L.append(f"  {lbl:<44}  М1: {str(m1):<14}  М2: {m2}")

        it = res["итого"]
        kl = res["колонны"]

        L.append("=" * 70)
        L.append("  МЕТАЛЛОЁМКОСТЬ ПРОИЗВОДСТВЕННОГО ЗДАНИЯ  v3.0")
        L.append("=" * 70)
        L.append(f"  Пролётов: {len(spans)}  |  L_стр={gp['L_build']}м")
        L.append(f"  Снег={gp['Q_snow']} кН/м²  |  Пыль={gp['Q_dust']} кН/м²  |  Технол.={gp['Q_tech']} кН/м²  |  γc={gp['yc']}")
        for i, sp in enumerate(spans):
            mf = CRANE_MODE_FACTOR[sp["crane_mode"]]
            h_info = kl["высоты_пролётов"][i] if i < len(kl["высоты_пролётов"]) else {}
            L.append(
                f"  Пролёт {i+1}: L={sp['L_span']}м  B={sp['B_step']}м  кол.шаг={sp['col_step']}м"
                f"  УГР={sp['h_rail']}м  H_кол={h_info.get('H_full','?')}м"
                f"  Кран {sp['q_crane_t']}т×{sp['n_cranes']}  {sp['crane_mode']}(×{mf})"
                f"  Ферма: {sp['truss_type']}"
            )
            L.append(
                f"           Кровля={sp['Q_roof']} кН/м²  Прогон={sp['Q_purlin']} кН/м²"
                f"  Ригели={sp['rig_load']} кг/м.п.  Стойка={'да' if sp['has_post'] else 'нет'}"
                f"  Тип: {sp['bld_type']}"
            )
        L.append("=" * 70)

        # ── ИТОГО (вверху) ──────────────────────────────
        L.append(f"\n{'━'*70}")
        L.append(f"  ★ ОБЩАЯ МЕТАЛЛОЁМКОСТЬ: {it['min_т']} т  ...  {it['max_т']} т")
        L.append(f"  ★ Метод 1: {it['М1_т']} т ({it['М1_кгм2']} кг/м²)   "
                 f"Метод 2: {it['М2_т']} т ({it['М2_кгм2']} кг/м²)")
        L.append(f"  ★ Площадь пола: {it['S_floor']} м²")
        L.append(f"{'━'*70}")

        # 1. Прогоны
        h("1. ПРОГОНЫ  [Метод 1 — формула]")
        pr = res["прогоны"]
        rw("Масса ИТОГО, т:", pr["масса_общая_т"])
        for d in pr["по_пролётам"]:
            rw(f"  Пролёт {d['пролёт']}  {d['профиль']}",
               f"q={d['нагрузка_тм']} т/м", f"{d['расход_кгм2']} кг/м²", f"{d['масса_т']} т")

        # 2. Фермы
        h("2. СТРОПИЛЬНЫЕ ФЕРМЫ  [М1 + М2]")
        fm = res["фермы"]
        r2("Масса ИТОГО, т:", fm["масса_общая_т_М1"], fm["масса_общая_т_М2"])
        for d in fm["по_пролётам"]:
            r2(f"  Пролёт {d['пролёт']}  (q={d['нагрузка_тм']} т/м):",
               d["G_М1_т"], d["G_М2_т"])

        # 3. Связи
        h("3. СВЯЗИ ПОКРЫТИЯ  [Метод 2 — таблица]")
        sv = res["связи_покрытия"]
        rw("Расход средний, кг/м²:", sv["расход_кгм2"])
        rw("Масса ИТОГО, т:", sv["масса_общая_т"])
        for d in sv.get("по_пролётам", []):
            rw(f"  Пролёт {d['пролёт']}:",
               f"{d['расход_кгм2']} кг/м²", f"{d['масса_т']} т")

        # 4. Подстропильные
        h("4. ПОДСТРОПИЛЬНЫЕ ФЕРМЫ  [М1 + М2]")
        psf = res["подстропильные_фермы"]
        if "примечание" in psf:
            L.append(f"  {psf['примечание']}")
        else:
            r2("Масса ИТОГО, т:", psf["масса_общая_т_М1"], psf["масса_общая_т_М2"])
            for d in psf.get("по_пролётам", []):
                if d.get("G_М1_т", 0) == 0 and d.get("G_М2_т") == "н/п":
                    continue
                r2(f"  Пролёт {d['пролёт']}  R={d['R_кн']} кН:",
                   d["G_М1_т"], d["G_М2_т"])

        # 5. Подкрановые
        h("5. ПОДКРАНОВЫЕ БАЛКИ  [М1 + М2]")
        pb = res["подкрановые_балки"]
        r2("Масса ИТОГО, т:", pb["масса_общая_т_М1"], pb["масса_общая_т_М2"])
        for d in pb["ряды_колонн"]:
            rw(f"  {d['ряд']}  (q={d['q']} т):", f"М1={d['G_М1_т']} т")

        # 6. Колонны
        h("6. КОЛОННЫ  [Метод 1 — формула]")
        rw("Кол-во колонн:", kl["n_колонн"])
        # Показать высоты по пролётам
        hts = kl.get("высоты_пролётов", [])
        if len(hts) == 1:
            rw("H_кол (полная), м:",
               hts[0]["H_full"],
               f"(надкр={hts[0]['H_upper']}м  подкр={hts[0]['H_lower']}м)")
        else:
            for ht in hts:
                rw(f"  Пролёт {ht['пролёт']} H_кол, м:",
                   ht["H_full"],
                   f"(надкр={ht['H_upper']}м  подкр={ht['H_lower']}м)")
        rw("Расход, кг/м²:", kl["расход_кгм2"])
        rw("Масса ИТОГО, т:", kl["масса_общая_т"])
        for d in kl["по_рядам"]:
            rw(f"  {d['ряд']}: 1 кол.={d['масса_1_кг']} кг", f"ряд={d['масса_ряд_т']} т")

        # 7. Фахверк
        h("7. ФАХВЕРК  [Метод 2 — таблица]")
        fh = res["фахверк"]
        if "ошибка" in fh and fh["масса_общая_т"] == 0:
            L.append(f"  Ошибка: {fh['ошибка']}")
        else:
            rw("Расход, кг/м² стен:", fh.get("расход_кгм2_стены", "н/п"))
            rw("Площадь стен, м²:",   fh.get("площадь_стен_м2", "н/п"))
            rw("Масса ИТОГО, т:",     fh.get("масса_общая_т", "н/п"))
            for d in fh.get("по_пролётам", []):
                if "ошибка" in d:
                    L.append(f"  Пролёт {d['пролёт']}: {d['ошибка']}")
                else:
                    rw(f"  Пролёт {d['пролёт']}:", f"{d['расход_кгм2_стены']} кг/м²", f"{d['масса_т']} т")

        # 8. Ограждение
        h("8. ОГРАЖДАЮЩИЕ КОНСТРУКЦИИ (справочно)")
        og = res["ограждение"]
        rw("Площадь стен, м²:", og["стены_м2"])
        rw("Площадь кровли, м²:", og["кровля_м2"])

        # 9. Опоры
        h("9. ОПОРЫ ТРУБОПРОВОДОВ  [Метод 2]")
        op = res["опоры_трубопроводов"]
        rw("Расход средний, кг/м²:", op["расход_кгм2"])
        rw("Масса ИТОГО, т:", op["масса_общая_т"])
        for d in op.get("по_пролётам", []):
            rw(f"  Пролёт {d['пролёт']}  ({spans[d['пролёт']-1]['bld_type']}):",
               f"{d['расход_кгм2']} кг/м²", f"{d['масса_т']} т")

        # Итого (повтор внизу)
        L.append(f"\n{'='*70}")
        L.append("  ИТОГО ПО КАРКАСУ (гибридное суммирование)")
        L.append("  Состав М1: прогоны(М1)+фермы(М1)+подстроп(М1)+подкран(М1)")
        L.append("            +колонны(М1)+связи(М2)+фахверк(М2)+опоры(М2)")
        L.append("  Состав М2: прогоны(М1)+фермы(М2)+подстроп(М2)+подкран(М2)")
        L.append("            +колонны(М1)+связи(М2)+фахверк(М2)+опоры(М2)")
        L.append(f"{'='*70}")
        L.append(f"  {'Метод 1 (формулы):':<46} {it['М1_т']} т  ({it['М1_кгм2']} кг/м²)")
        L.append(f"  {'Метод 2 (таблицы):':<46} {it['М2_т']} т  ({it['М2_кгм2']} кг/м²)")
        L.append(f"{'━'*70}")
        L.append(f"  ★ ДИАПАЗОН: {it['min_т']} т  ...  {it['max_т']} т")
        L.append(f"{'━'*70}")

        if res.get("_log"):
            L.append("\n─── Лог расчёта ─────────────────────────────────────────────────────")
            for entry in res["_log"]:
                L.append(f"  {entry}")

        text = "\n".join(L)
        self._last_results_text = text
        self._set_txt(text)


# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    App().mainloop()
