#!/usr/bin/env python3
"""
Металлоёмкость производственных зданий — десктопная версия v2.0
Поддержка: многопролётные здания, кровельный пирог, режимы кранов,
           коррекция высоты колонн, гибридное суммирование.
БЭКАП v1.0 → main_desktop_backup_v1.py
"""
import math
import traceback
import customtkinter as ctk
from tkinter import messagebox

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
#  ОСНОВНОЙ РАСЧЁТ — многопролётная версия
# ─────────────────────────────────────────────────────────

def calculate(gp: dict, spans: list) -> dict:
    """
    gp   — глобальные параметры здания
    spans — список пролётов: [{"L_span", "q_crane_t", "n_cranes",
                                "with_pass", "crane_mode", "truss_type"}, ...]
    Колонны: N пролётов → N+1 рядов колонн.
    Крайние ряды (2 шт.) — несут нагрузку от 1 пролёта.
    Средние ряды (N-1 шт.) — от 2 соседних пролётов.
    """
    res = {}
    log = []

    L_build   = gp["L_build"]
    B_step    = gp["B_step"]
    col_step  = gp["col_step"]
    h_rail    = gp["h_rail"]
    Q_snow    = gp["Q_snow"]
    Q_dust    = gp["Q_dust"]
    Q_roof    = gp["Q_roof"]       # сумма кровельного пирога
    Q_tech    = gp["Q_tech"]       # П.3: технологическая нагрузка
    Q_purlin  = gp["Q_purlin"]
    yc        = gp["yc"]
    rig_load  = gp["rig_load"]
    has_post  = gp["has_post"]
    bld_type  = gp["bld_type"]
    H_col_ov  = gp.get("H_col_override", 0.0) or 0.0

    N = len(spans)
    W_build   = sum(s["L_span"] for s in spans)
    S_floor   = L_build * W_build
    P_walls   = 2 * (L_build + W_build)

    # ── П.5: Высота колонны ─────────────────────────────
    # Правильная формула: H_full = УГР + 4.5 м
    H_lower  = h_rail
    H_upper  = 4.5   # надкрановая часть (фиксированная)
    H_full   = H_lower + H_upper
    if H_col_ov > H_lower:
        H_full  = H_col_ov
        H_upper = H_full - H_lower
    S_walls = P_walls * H_full

    log.append(f"Пролётов: {N}  W={W_build:.0f}м  S_пола={S_floor:.0f}м²")
    log.append(f"H_кол={H_full:.2f}м (УГР={H_lower:.1f}м + 4.5м надкр.)")

    # ── 1+2. Прогоны и фермы — по пролётам ─────────────
    g_links = 0.05
    Q_load_total = Q_roof + Q_purlin + Q_snow + Q_dust + Q_tech  # кН/м²
    gn_total     = Q_load_total + g_links

    G_pur_all_t  = 0.0
    G_tr_m1_all  = 0.0   # суммарная масса ферм М1 (т)
    G_tr_m2_all  = 0.0
    span_data    = []

    for i, sp in enumerate(spans):
        L  = sp["L_span"]
        tt = sp["truss_type"]
        Ss = L_build * L

        # Прогоны
        qp_tm = Q_load_total * 3.0 * yc / 9.81
        mp, pname = select_purlin(qp_tm, B_step)
        n_pr = L / 3.0 + 3
        g_pur = mp * n_pr / (L * B_step)
        G_pur_t = g_pur * Ss / 1000
        G_pur_all_t += G_pur_t

        # Фермы — нагрузка
        Q_tm = gn_total * B_step * yc / 9.81
        n_tr = L_build / B_step + 1

        # М1 (только Уголки)
        G_tr1 = None
        if tt == "Уголки":
            Gkn = (gn_total*B_step/1000 + 0.018)*1.4*L**2/0.85*yc
            G_tr1 = Gkn/9.81 * n_tr          # общая масса ферм в пролёте, т
            G_tr_m1_all += G_tr1

        # М2 (таблица)
        G_tr2 = None
        mt = get_truss_mass_m2(tt, L, Q_tm)
        if mt is not None:
            G_tr2 = mt * n_tr               # т
            G_tr_m2_all += G_tr2

        span_data.append({
            "idx": i+1, "L_span": L, "S_span": Ss, "tt": tt,
            "purlin": pname, "qp_tm": round(qp_tm, 3),
            "g_pur_kgm2": round(g_pur, 2), "G_pur_t": round(G_pur_t, 2),
            "Q_tm": round(Q_tm, 3),
            "G_tr_m1": round(G_tr1, 2) if G_tr1 else "н/п",
            "G_tr_m2": round(G_tr2, 2) if G_tr2 else "н/п",
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

    # ── 3. Связи покрытия ────────────────────────────────
    q_max_crane = max(s["q_crane_t"] for s in spans)
    g_br = get_bracing_kgm2(q_max_crane, B_step)
    res["связи_покрытия"] = {
        "расход_кгм2": g_br,
        "масса_общая_т": round(g_br * S_floor / 1000, 2),
    }

    # ── 4. Подстропильные фермы ──────────────────────────
    G_sub_m1 = 0.0
    G_sub_m2 = 0.0
    sub_rows = []
    if col_step == 12 and B_step < col_step:
        n_bays = L_build / col_step
        for i, sp in enumerate(spans):
            L = sp["L_span"]
            Q_tm = gn_total * B_step * yc / 9.81
            R_kn = gn_total * B_step * yc * L / 2
            R_t  = R_kn / 9.81
            Rf   = max(100, min(R_kn, 400))
            apf  = (Rf - 100)*0.0002 + 0.044
            G1   = apf * 144 * n_bays / N          # т (пропорционально)
            G_sub_m1 += G1
            mt = get_subtruss_mass_m2(R_t)
            G2 = mt * n_bays / N if mt else None
            if G2: G_sub_m2 += G2
            sub_rows.append({"пролёт":i+1,"R_кн":round(R_kn,1),
                "G_М1_т":round(G1,2),"G_М2_т":round(G2,2) if G2 else "н/п"})
        res["подстропильные_фермы"] = {
            "масса_общая_т_М1": round(G_sub_m1, 2),
            "масса_общая_т_М2": round(G_sub_m2, 2),
            "по_пролётам": sub_rows,
        }
    else:
        res["подстропильные_фермы"] = {"примечание": "Не требуются"}

    # ── 5. Подкрановые балки — по рядам колонн ──────────
    # N пролётов → N+1 рядов:
    # Ряд 0 (крайний лев): кран пролёта 0, is_edge=True
    # Ряд i (средний 1..N-1): краны пролётов i-1 и i, is_edge=False
    # Ряд N (крайний прав): кран пролёта N-1, is_edge=True

    L_pb = float(col_step)
    n_bays_a = math.ceil(L_build / col_step)
    G_pb_m1 = 0.0
    G_pb_m2 = 0.0
    G_pb_kn_repr = 0.0   # для расчёта колонны (репрезентативное значение)
    pb_rows = []

    def _pb_row(sp_obj, is_edge, label):
        nonlocal G_pb_m1, G_pb_m2, G_pb_kn_repr
        q = sp_obj["q_crane_t"]; nc = sp_obj["n_cranes"]
        wp = sp_obj["with_pass"]
        mf = CRANE_MODE_FACTOR[sp_obj["crane_mode"]]
        alp = _lkp(CRANE_BEAM_ALPHA, q)
        qr  = _lkp(RAIL_WEIGHT_KN, q)
        G1t = (alp*L_pb + qr)*L_pb*1.4/9.81
        Gkn = (alp*L_pb + qr)*L_pb*1.4
        G_pb_m1     += G1t * n_bays_a
        G_pb_kn_repr = max(G_pb_kn_repr, Gkn)
        pb_kgm = get_crane_beam_kgm(q, L_pb, nc)
        br_kgm = get_brake_kgm(q, L_pb, nc, wp, is_edge)
        if pb_kgm and br_kgm is not None:
            G_pb_m2 += (pb_kgm*mf + br_kgm*mf)*L_pb*n_bays_a/1000
        pb_rows.append({"ряд":label,"G_М1_т":round(G1t*n_bays_a,2),"q":q})

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

    # ── 6. Колонны — с учётом топологии ────────────────────
    rho=78.5; pu=1.4; pl=2.1; kMu=0.275; kMl=0.45
    gst=0.25; aw=0.15

    def _col_kg(L_sp, q_cr, H_up, H_lo):
        Gwu = gst*H_up*(1-aw)*col_step
        Gwl = gst*H_lo*(1-aw)*col_step
        SFv = Q_load_total*col_step*L_sp/2 + Gwu
        Gcu = SFv*rho*pu*H_up/(kMu*24000)
        qeq = _lkp(CRANE_Q_EQUIV, q_cr)
        D   = qeq*col_step*1.1*yc
        alp = _lkp(CRANE_BEAM_ALPHA, q_cr)
        qrr = _lkp(RAIL_WEIGHT_KN, q_cr)
        Gpb = (alp*L_pb + qrr)*L_pb*1.4
        SFn = SFv + D + Gpb + Gwl + Gcu
        Gcl = SFn*rho*pl*H_lo/(kMl*24000)
        return (Gcu+Gcl)/9.81*1000

    n_col_along = round(L_build/col_step)+1
    G_cols_t = 0.0
    col_rows_detail = []

    # Крайний левый ряд
    Gce = _col_kg(spans[0]["L_span"], spans[0]["q_crane_t"], H_upper, H_lower)
    G_cols_t += Gce*n_col_along/1000
    col_rows_detail.append({"ряд":"Крайний Л","масса_1_кг":round(Gce,1),"масса_ряд_т":round(Gce*n_col_along/1000,2)})

    # Средние ряды
    for mi in range(1, N):
        sL = spans[mi-1]; sR = spans[mi]
        Gwu = gst*H_upper*(1-aw)*col_step
        Gwl = gst*H_lower*(1-aw)*col_step
        SFv = Q_load_total*col_step*(sL["L_span"]+sR["L_span"])/2 + Gwu
        Gcu = SFv*rho*pu*H_upper/(kMu*24000)
        qeqL = _lkp(CRANE_Q_EQUIV, sL["q_crane_t"])
        qeqR = _lkp(CRANE_Q_EQUIV, sR["q_crane_t"])
        D = (qeqL+qeqR)*col_step*1.1*yc
        alpL=_lkp(CRANE_BEAM_ALPHA,sL["q_crane_t"]); qrL=_lkp(RAIL_WEIGHT_KN,sL["q_crane_t"])
        alpR=_lkp(CRANE_BEAM_ALPHA,sR["q_crane_t"]); qrR=_lkp(RAIL_WEIGHT_KN,sR["q_crane_t"])
        Gpb = ((alpL*L_pb+qrL)*L_pb*1.4 + (alpR*L_pb+qrR)*L_pb*1.4)
        SFn = SFv + D + Gpb + Gwl + Gcu
        Gcl = SFn*rho*pl*H_lower/(kMl*24000)
        Gcm_kg = (Gcu+Gcl)/9.81*1000
        G_cols_t += Gcm_kg*n_col_along/1000
        col_rows_detail.append({"ряд":f"Средний {mi}","масса_1_кг":round(Gcm_kg,1),"масса_ряд_т":round(Gcm_kg*n_col_along/1000,2)})

    # Крайний правый ряд
    Gce2 = _col_kg(spans[N-1]["L_span"], spans[N-1]["q_crane_t"], H_upper, H_lower)
    G_cols_t += Gce2*n_col_along/1000
    col_rows_detail.append({"ряд":"Крайний П","масса_1_кг":round(Gce2,1),"масса_ряд_т":round(Gce2*n_col_along/1000,2)})

    n_col_total = n_col_along*(N+1)
    res["колонны"] = {
        "n_колонн": n_col_total,
        "H_full_м": round(H_full,2), "H_upper_м": round(H_upper,2), "H_lower_м": round(H_lower,2),
        "расход_кгм2": round(G_cols_t*1000/S_floor, 2),
        "масса_общая_т": round(G_cols_t, 2),
        "по_рядам": col_rows_detail,
    }

    # ── 7. Фахверк ──────────────────────────────────────
    gf = get_fakhverk_kgm2(col_step, has_post, H_full, rig_load)
    if gf:
        res["фахверк"] = {"расход_кгм2_стены":gf,"площадь_стен_м2":round(S_walls,1),
                          "масса_общая_т":round(gf*S_walls/1000,2)}
    else:
        res["фахверк"] = {"ошибка":"Не определён","масса_общая_т":0}

    # ── 8. Ограждение ───────────────────────────────────
    res["ограждение"] = {"стены_м2":round(S_walls,1),"кровля_м2":round(S_floor,1)}

    # ── 9. Опоры трубопроводов ──────────────────────────
    gp2 = get_pipe_support_kgm2(bld_type)
    res["опоры_трубопроводов"] = {
        "расход_кгм2": gp2,
        "масса_общая_т": round(gp2*S_floor/1000, 2),
    }

    # ── П.6: Гибридное суммирование ─────────────────────
    # Элементы только в М1: прогоны, колонны → в оба итога
    # Элементы только в М2: связи, фахверк, опоры → в оба итога
    # Элементы в М1 и М2: фермы, подстроп., подкрановые → берём соотв. метод
    def sv(d, *keys):
        for k in keys:
            v = d.get(k)
            if isinstance(v, (int, float)): return float(v)
        return 0.0

    # Общие (одинаковы в М1 и М2)
    common = (
        sv(res["прогоны"],           "масса_общая_т")
        + sv(res["колонны"],         "масса_общая_т")
        + sv(res["связи_покрытия"],  "масса_общая_т")
        + sv(res["фахверк"],         "масса_общая_т")
        + sv(res["опоры_трубопроводов"], "масса_общая_т")
    )

    # Специфика М1: фермы(М1) + подстроп(М1) + подкрановые(М1)
    m1_spec = (
        sv(res["фермы"],                    "масса_общая_т_М1")
        + sv(res["подстропильные_фермы"],   "масса_общая_т_М1")
        + sv(res["подкрановые_балки"],      "масса_общая_т_М1")
    )

    # Специфика М2: фермы(М2) + подстроп(М2) + подкрановые(М2)
    m2_spec = (
        sv(res["фермы"],                    "масса_общая_т_М2")
        + sv(res["подстропильные_фермы"],   "масса_общая_т_М2")
        + sv(res["подкрановые_балки"],      "масса_общая_т_М2")
    )

    total_m1 = common + m1_spec
    total_m2 = common + m2_spec

    res["итого"] = {
        "М1_т":    round(total_m1, 2),
        "М2_т":    round(total_m2, 2),
        "М1_кгм2": round(total_m1*1000/S_floor, 2) if S_floor else 0,
        "М2_кгм2": round(total_m2*1000/S_floor, 2) if S_floor else 0,
        "min_т":   round(min(total_m1, total_m2), 2),
        "max_т":   round(max(total_m1, total_m2), 2),
        "S_floor": round(S_floor, 1),
    }
    res["_log"] = log
    return res


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
    """Карточка одного пролёта."""

    def __init__(self, parent, span_num: int, on_remove):
        super().__init__(parent, fg_color="#1e2a3a", corner_radius=8)
        self._num = span_num
        self._on_remove = on_remove
        self._build(span_num)

    def _build(self, n):
        # Заголовок
        hdr = ctk.CTkFrame(self, fg_color="#243347", corner_radius=6)
        hdr.pack(fill="x", padx=6, pady=(6,2))
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

        r = 0
        def lbl(text):
            nonlocal r
            ctk.CTkLabel(body, text=text, font=FL, anchor="w").grid(
                row=r, column=0, sticky="w", **PAD)
        def fe(default):
            nonlocal r
            e = FloatEntry(body, width=110)
            e.insert(0, str(default))
            e.grid(row=r, column=1, sticky="w", **PAD)
            r += 1
            return e
        def cmb(values, default=None):
            nonlocal r
            v = ctk.StringVar(value=default or values[0])
            c = ctk.CTkComboBox(body, values=values, variable=v, width=160)
            c.grid(row=r, column=1, sticky="w", **PAD)
            r += 1
            return v

        lbl("Пролёт фермы L, м:");       r+=1; self.e_L   = fe(24)
        lbl("Тип фермы:");                r+=1; self.v_tt  = cmb(["Уголки","Двутавры","Молодечно"])
        lbl("Г/п крана, т:");             r+=1; self.e_q   = fe(50)
        lbl("Кранов в пролёте:");         r+=1; self.v_nc  = cmb(["1","2"])
        lbl("Тормозные пути:");           r+=1; self.v_wp  = cmb(["С проходом","Без прохода"])
        # П.4: Режим работы кранов
        lbl("Режим работы крана:");       r+=1; self.v_cm  = cmb(list(CRANE_MODE_FACTOR.keys()), "Режим 1-6К")

    def update_title(self, n):
        self._num = n
        self._lbl.configure(text=f"  Пролёт {n}")

    def get_params(self) -> dict:
        return {
            "L_span":     self.e_L.get_float(24),
            "q_crane_t":  self.e_q.get_float(50),
            "n_cranes":   int(self.v_nc.get()),
            "with_pass":  self.v_wp.get() == "С проходом",
            "crane_mode": self.v_cm.get(),
            "truss_type": self.v_tt.get(),
        }


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Металлоёмкость производственных зданий v2.0")
        self.geometry("1520x960")
        self.resizable(True, True)
        self._span_frames: list[SpanFrame] = []
        self._build_ui()

    # ── Построение интерфейса ────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # ─ Левая панель ─────────────────────────────────
        left = ctk.CTkScrollableFrame(self, label_text="Входные параметры", width=520)
        left.grid(row=0, column=0, sticky="nsew", padx=(10,5), pady=10)
        left.columnconfigure(1, weight=1)

        self._r = 0

        def sec(t):
            ctk.CTkLabel(left, text=t, font=FT, text_color="#4fc3f7").grid(
                row=self._r, column=0, columnspan=2, sticky="w", **PAD)
            self._r += 1

        def ent(lbl, default):
            ctk.CTkLabel(left, text=lbl, font=FL, anchor="w").grid(
                row=self._r, column=0, sticky="w", **PAD)
            e = FloatEntry(left, width=120)
            e.insert(0, str(default))
            e.grid(row=self._r, column=1, sticky="w", **PAD)
            self._r += 1
            return e

        def cmb(lbl, vals, default=None):
            ctk.CTkLabel(left, text=lbl, font=FL, anchor="w").grid(
                row=self._r, column=0, sticky="w", **PAD)
            v = ctk.StringVar(value=default or vals[0])
            c = ctk.CTkComboBox(left, values=vals, variable=v, width=160)
            c.grid(row=self._r, column=1, sticky="w", **PAD)
            self._r += 1
            return v

        def chk(lbl, default=False):
            v = ctk.BooleanVar(value=default)
            c = ctk.CTkCheckBox(left, text=lbl, variable=v, font=FL)
            c.grid(row=self._r, column=0, columnspan=2, sticky="w", **PAD)
            self._r += 1
            return v

        # Геометрия
        sec("Геометрия здания")
        self.e_L_build  = ent("Длина по осям, м", 120)
        self.e_B_step   = ent("Шаг ферм B, м", 6)
        self.v_col_step = cmb("Шаг колонн, м", ["6","12"], "12")
        self.e_h_rail   = ent("Уровень головки рельса (УГР), м", 8.0)

        # П.5: Коррекция высоты (опционально)
        sec("Высота колонны (авто = УГР + 4.5 м)")
        self.e_h_col_ov = ent("Переопределить H_кол, м (0 = авто)", 0)

        # Нагрузки
        sec("Нагрузки (расчётные, кН/м²)")
        self.e_Q_snow   = ent("Снег Qснег", 2.1)
        self.e_Q_dust   = ent("Пыль Qпыль", 0.0)
        # П.3: Технологическая нагрузка
        self.e_Q_tech   = ent("Технол. нагрузка (пром. проводки/обор.), кН/м²", 0.0)
        self.e_Q_purlin = ent("Вес прогона Qвес.прог., кН/м²", 0.35)
        self.e_yc       = ent("Коэф. ответственности γc", 1.0)

        # П.2: Кровельный пирог
        sec("Кровельный пирог (Qкровля считается автоматически)")
        self._roof_vars: dict[str, ctk.BooleanVar] = {}
        for mat, w in ROOF_MATERIALS.items():
            v = ctk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(left, text=f"{mat}  [{w:.2f} кН/м²]",
                                  variable=v, font=FH,
                                  command=self._update_roof_label)
            cb.grid(row=self._r, column=0, columnspan=2, sticky="w",
                    padx=PAD["padx"], pady=1)
            self._r += 1
            self._roof_vars[mat] = v

        self.lbl_roof_sum = ctk.CTkLabel(
            left, text="Qкровля = 0.00 кН/м²", font=FL, text_color="#ffcc80")
        self.lbl_roof_sum.grid(row=self._r, column=0, columnspan=2,
                                sticky="w", **PAD)
        self._r += 1

        # Фахверк
        sec("Фахверк")
        self.e_rig_load = ent("Нагрузка на ригели, кг/м.п.", 0)
        self.v_has_post = chk("Стойка фахверка (шаг 12м)")

        # Тип здания
        sec("Тип здания")
        self.v_bld_type = cmb("Тип здания",
            ["Основные производственные","Здания энергоносителей","Вспомогательные здания"])

        # Кнопки
        self._r += 1
        btn_fr = ctk.CTkFrame(left, fg_color="transparent")
        btn_fr.grid(row=self._r, column=0, columnspan=2, pady=8)
        ctk.CTkButton(btn_fr, text="  Рассчитать", font=FT, width=180, height=44,
                      fg_color="#1565c0", hover_color="#0d47a1",
                      command=self._on_calculate).pack(side="left", padx=5)
        ctk.CTkButton(btn_fr, text="Очистить", font=FL, width=100, height=44,
                      fg_color="#37474f", hover_color="#263238",
                      command=self._on_clear).pack(side="left", padx=5)
        self._r += 1

        # Пролёты
        sec("─── Пролёты здания ───────────────────────────────")
        self._spans_container = ctk.CTkFrame(left, fg_color="transparent")
        self._spans_container.grid(row=self._r, column=0, columnspan=2, sticky="ew")
        self._r += 1

        add_btn_row = ctk.CTkFrame(left, fg_color="transparent")
        add_btn_row.grid(row=self._r, column=0, columnspan=2, pady=4)
        ctk.CTkButton(add_btn_row, text="＋ Добавить пролёт", font=FL,
                      fg_color="#1b5e20", hover_color="#2e7d32",
                      command=self._add_span).pack()
        self._r += 1

        # Добавить 1 пролёт по умолчанию
        self._add_span()

        # ─ Правая панель ────────────────────────────────
        right = ctk.CTkFrame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(5,10), pady=10)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Результаты расчёта", font=FT
                     ).grid(row=0, column=0, sticky="w", padx=10, pady=(10,0))
        self.txt = ctk.CTkTextbox(right, font=FRE, wrap="word", state="disabled")
        self.txt.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5,10))

        self.lbl_status = ctk.CTkLabel(self, text="", font=FL, text_color="#80cbc4")
        self.lbl_status.grid(row=1, column=0, columnspan=2, sticky="w", padx=20, pady=(0,8))

    # ── Кровельный пирог ────────────────────────────────

    def _update_roof_label(self):
        total = sum(ROOF_MATERIALS[m]*v.get() for m, v in self._roof_vars.items())
        self.lbl_roof_sum.configure(text=f"Qкровля = {total:.2f} кН/м²")

    def _get_Q_roof(self) -> float:
        return sum(ROOF_MATERIALS[m]*v.get() for m, v in self._roof_vars.items())

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
            f.update_title(i+1)

    # ── Параметры ────────────────────────────────────────

    def _read_global_params(self) -> dict:
        Q_roof = self._get_Q_roof()
        if Q_roof == 0.0:
            # Если пирог не выбран — читаем старый стиль как 0 (предупредим)
            pass
        return {
            "L_build":       self.e_L_build.get_float(120),
            "B_step":        self.e_B_step.get_float(6),
            "col_step":      int(self.v_col_step.get()),
            "h_rail":        self.e_h_rail.get_float(8),
            "H_col_override":self.e_h_col_ov.get_float(0),
            "Q_snow":        self.e_Q_snow.get_float(2.1),
            "Q_dust":        self.e_Q_dust.get_float(0),
            "Q_tech":        self.e_Q_tech.get_float(0),
            "Q_roof":        Q_roof,
            "Q_purlin":      self.e_Q_purlin.get_float(0.35),
            "yc":            self.e_yc.get_float(1.0),
            "rig_load":      self.e_rig_load.get_float(0),
            "has_post":      self.v_has_post.get(),
            "bld_type":      self.v_bld_type.get(),
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
            if gp["Q_roof"] == 0.0:
                if not messagebox.askyesno("Кровельный пирог не выбран",
                    "Нагрузка от кровли = 0. Продолжить расчёт?"):
                    self.lbl_status.configure(text="Отменено.", text_color="#ef9a9a")
                    return
            res = calculate(gp, spans)
            self._show_results(gp, spans, res)
            self.lbl_status.configure(text="Расчёт завершён.", text_color="#80cbc4")
        except Exception:
            tb = traceback.format_exc()
            messagebox.showerror("Ошибка расчёта", tb)
            self.lbl_status.configure(text="Ошибка.", text_color="#ef9a9a")

    def _on_clear(self):
        self._set_txt("")
        self.lbl_status.configure(text="")

    def _set_txt(self, text: str):
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", text)
        self.txt.configure(state="disabled")

    # ── Вывод результатов ────────────────────────────────

    def _show_results(self, gp, spans, res):
        L  = []
        S  = "─" * 70

        def h(t):  L.append(f"\n{S}\n  {t}\n{S}")
        def rw(lbl, *vs): L.append(f"  {lbl:<44}  {'  '.join(str(v) for v in vs)}")
        def r2(lbl, m1, m2): L.append(f"  {lbl:<44}  М1: {str(m1):<14}  М2: {m2}")

        it = res["итого"]

        L.append("=" * 70)
        L.append("  МЕТАЛЛОЁМКОСТЬ ПРОИЗВОДСТВЕННОГО ЗДАНИЯ  v2.0")
        L.append("=" * 70)
        L.append(f"  Пролётов: {len(spans)}  |  L_стр={gp['L_build']}м  |  Шаг ферм={gp['B_step']}м  |  Шаг кол.={gp['col_step']}м")
        L.append(f"  УГР={gp['h_rail']}м  |  H_кол={res['колонны']['H_full_м']}м  |  Q_кровля={gp['Q_roof']:.2f} кН/м²")
        for i, sp in enumerate(spans):
            mf = CRANE_MODE_FACTOR[sp["crane_mode"]]
            L.append(f"  Пролёт {i+1}: L={sp['L_span']}м  Кран {sp['q_crane_t']}т×{sp['n_cranes']}  {sp['crane_mode']}(×{mf})  Ферма: {sp['truss_type']}")
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
        rw("Расход, кг/м²:", sv["расход_кгм2"])
        rw("Масса ИТОГО, т:", sv["масса_общая_т"])

        # 4. Подстропильные
        h("4. ПОДСТРОПИЛЬНЫЕ ФЕРМЫ  [М1 + М2]")
        psf = res["подстропильные_фермы"]
        if "примечание" in psf:
            L.append(f"  {psf['примечание']}")
        else:
            r2("Масса ИТОГО, т:", psf["масса_общая_т_М1"], psf["масса_общая_т_М2"])
            for d in psf.get("по_пролётам", []):
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
        kl = res["колонны"]
        rw("Кол-во колонн:", kl["n_колонн"])
        rw("H_кол (полная), м:", kl["H_full_м"], f"(надкр={kl['H_upper_м']}м  подкр={kl['H_lower_м']}м)")
        rw("Расход, кг/м²:", kl["расход_кгм2"])
        rw("Масса ИТОГО, т:", kl["масса_общая_т"])
        for d in kl["по_рядам"]:
            rw(f"  {d['ряд']}: 1 кол.={d['масса_1_кг']} кг", f"ряд={d['масса_ряд_т']} т")

        # 7. Фахверк
        h("7. ФАХВЕРК  [Метод 2 — таблица]")
        fh = res["фахверк"]
        if "ошибка" in fh:
            L.append(f"  Ошибка: {fh['ошибка']}")
        else:
            rw("Расход, кг/м² стен:", fh.get("расход_кгм2_стены","н/п"))
            rw("Площадь стен, м²:",   fh.get("площадь_стен_м2","н/п"))
            rw("Масса ИТОГО, т:",     fh.get("масса_общая_т","н/п"))

        # 8. Ограждение
        h("8. ОГРАЖДАЮЩИЕ КОНСТРУКЦИИ (справочно)")
        og = res["ограждение"]
        rw("Площадь стен, м²:", og["стены_м2"])
        rw("Площадь кровли, м²:", og["кровля_м2"])

        # 9. Опоры
        h("9. ОПОРЫ ТРУБОПРОВОДОВ  [Метод 2]")
        op = res["опоры_трубопроводов"]
        rw("Расход, кг/м²:", op["расход_кгм2"])
        rw("Масса ИТОГО, т:", op["масса_общая_т"])

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

        self._set_txt("\n".join(L))


# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    App().mainloop()
