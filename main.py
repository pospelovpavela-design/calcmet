#!/usr/bin/env python3
"""
Металлоёмкость производственных зданий — iOS v2.0
Многопролётный расчёт, экспорт результатов, safe-area.
Расчётное ядро идентично desktop v3.0 (Ry=240000, CRANE_Q_EQUIV ×2.5, коэф.режима 1.80).
"""
import os, sys, math, traceback
from datetime import datetime

# ── Сохранение краша ────────────────────────────────────────
def _save_crash(exc_type, exc_value, exc_tb):
    text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    docs = os.path.expanduser("~/Documents")
    os.makedirs(docs, exist_ok=True)
    for path in [
        os.path.join(docs, "metalcalc_crash.log"),
        os.path.join(os.path.expanduser("~"), "metalcalc_crash.log"),
    ]:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            break
        except Exception:
            continue
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = _save_crash

# ════════════════════════════════════════════════════════════
#  ДАННЫЕ — идентичны desktop v3.0
# ════════════════════════════════════════════════════════════

# Таблица прогонов: (qp_max т/м, имя B=6, масса_кг B=6, имя B=12, масса_кг B=12)
PURLIN_TABLE = [
    (0.45, "Швеллер 20",   110.4, "Двутавр 20",  345.0),
    (0.67, "Швеллер 22",   122.4, "Двутавр 24",  420.0),
    (0.87, "Швеллер 24",   134.4, "Двутавр 27",  492.0),
    (1.10, "Швеллер 27",   151.2, "Двутавр 30",  558.0),
    (1.30, "Швеллер 30",   168.0, "Двутавр 33",  624.0),
    (1.50, "Швеллер 33",   184.8, "Двутавр 36",  697.2),
]

CRANE_BEAM_ALPHA = {
    5:0.08, 10:0.09, 20:0.12, 32:0.15, 50:0.18,
    80:0.22, 100:0.26, 125:0.30, 200:0.36, 320:0.40, 400:0.45,
}
RAIL_WEIGHT_KN = {
    5:0.461, 10:0.461, 20:0.461, 32:0.598, 50:0.598,
    80:0.831, 100:1.135, 125:1.135, 200:1.135, 320:1.417, 400:1.417,
}
# Эквивалентная нагрузка вдоль подкрановой балки (кН/м), скорр. ×2.5
CRANE_Q_EQUIV = {
    5:20, 10:30, 20:50, 32:70, 50:95, 80:138,
    100:170, 125:200, 200:262, 320:362, 400:437,
}

# Коэффициенты режима работы крана
CRANE_MODE_FACTOR_M1 = {"Режим 1-6К": 1.00, "Режим 7-8К": 1.80}
CRANE_MODE_FACTOR_M2 = {"Режим 1-6К": 0.65, "Режим 7-8К": 1.80}
CRANE_MODES = list(CRANE_MODE_FACTOR_M1.keys())

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

_CB_Q1 = [5,10,20,32,50]; _CB_Q2 = [80,100,125,200,400]
CRANE_BEAM_T1 = {
    6:  [ 80, 90, 100,120, 150,185, 210,260, 270,330],
    12: [150,170, 190,230, 270,335, 375,455, 490,595],
}
CRANE_BEAM_T2 = {
    12: [290,330, 350,400, 430,490,  620, 720,  920,1080],
    18: [460,520, 540,615, 660,750,  950,1100, 1410,1640],
    24: [680,770, 800,910, 980,1110,1420,1640, 2100,2450],
}
BRAKE_T1 = {
    (6,True,True):[100,110],   (6,True,False):[65,70],
    (6,False,True):[120,140],  (6,False,False):[70,75],
    (12,True,True):[100,120],  (12,True,False):[65,70],
    (12,False,True):[100,120], (12,False,False):[70,75],
}
BRAKE_T2 = {
    (12,True,True):[120,140],  (12,True,False):[80,100],
    (12,False,True):[140,160], (12,False,False):[60,80],
    (18,True,True):[120,140],  (18,True,False):[80,100],
    (18,False,True):[140,160], (18,False,False):[80,100],
    (24,True,True):[220,240],  (24,True,False):[140,160],
    (24,False,True):[220,240], (24,False,False):[140,160],
}

PIPE_SUPPORT = {
    "Основные производственные": (11, 22),
    "Здания энергоносителей":    (23, 40),
    "Вспомогательные здания":    (2,  4),
}

TRUSS_TYPES = ["Уголки", "Двутавры", "Молодечно"]
BLD_TYPES   = list(PIPE_SUPPORT.keys())

# ════════════════════════════════════════════════════════════
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (desktop API)
# ════════════════════════════════════════════════════════════

def _lkp(d, val):
    for k in sorted(d):
        if val <= k: return d[k]
    return d[sorted(d)[-1]]

def ceil_to_table(target, values):
    for v in sorted(values):
        if target <= v: return v
    return sorted(values)[-1]

def interp_table(loads, masses, target):
    for i, ld in enumerate(loads):
        if target <= ld: return masses[i]
    return masses[-1]

def select_purlin(load_tm, B_step):
    for qmax, n6, m6, n12, m12 in PURLIN_TABLE:
        if load_tm <= qmax:
            return (m6, n6) if B_step <= 6 else (m12, n12)
    _, n6, m6, n12, m12 = PURLIN_TABLE[-1]
    n6 += "!"; n12 += "!"
    return (m6, n6) if B_step <= 6 else (m12, n12)

def get_truss_mass_m2(truss_type, span_m, load_tm):
    spans = sorted(TRUSS_MASSES.get(truss_type, {}).keys())
    if not spans: return None
    sk = ceil_to_table(span_m, spans)
    masses = TRUSS_MASSES[truss_type].get(sk)
    if masses is None: return None
    return interp_table(TRUSS_LOADS, masses, load_tm)

def get_subtruss_mass_m2(R_t):
    return interp_table(SUBTRUSS_LOADS, SUBTRUSS_MASSES,
                        ceil_to_table(R_t, SUBTRUSS_LOADS))

def get_bracing_kgm2(q_crane_t, step_farm_m):
    if q_crane_t <= 120: return 15.0 if step_farm_m <= 6 else 35.0
    return 40.0 if step_farm_m <= 6 else 55.0

def get_crane_beam_kgm(q_crane_t, span_pb_m, n_cranes):
    try:
        if q_crane_t <= 50: table, q_ord = CRANE_BEAM_T1, _CB_Q1
        else:               table, q_ord = CRANE_BEAM_T2, _CB_Q2
        span_key = ceil_to_table(span_pb_m, sorted(table.keys()))
        vals = table.get(span_key)
        if vals is None: return None
        qi = min(range(len(q_ord)), key=lambda i: abs(q_ord[i] - q_crane_t))
        ci = qi * 2 + (0 if n_cranes == 1 else 1)
        return vals[ci] if ci < len(vals) else None
    except Exception: return None

def get_brake_kgm(q_crane_t, span_pb_m, n_cranes, with_passage, is_edge):
    try:
        table = BRAKE_T1 if q_crane_t <= 50 else BRAKE_T2
        span_key = ceil_to_table(span_pb_m, sorted({k[0] for k in table}))
        vals = table.get((span_key, is_edge, with_passage))
        if vals is None:
            vals = next((v for k, v in table.items() if k[0] == span_key), None)
        if vals:
            return vals[0 if n_cranes == 1 else min(1, len(vals) - 1)]
    except Exception: pass
    return None

def get_fakhverk_kgm2(step_col, has_post, h_bld, rig_load):
    try:
        if step_col <= 6 and has_post: ft = 'III'
        elif step_col <= 6:            ft = 'I'
        else:                          ft = 'II'
        lc = 0 if rig_load <= 0 else (1 if rig_load <= 100 else 2)
        hc = 0 if h_bld <= 10 else (1 if h_bld <= 20 else 2)
        return FAKHVERK_DATA.get((ft, lc, hc))
    except Exception: return None

def get_pipe_support_kgm2(bld_type):
    lo, hi = PIPE_SUPPORT.get(bld_type, (11, 22))
    return (lo + hi) / 2

# ════════════════════════════════════════════════════════════
#  РАСЧЁТ — идентичен desktop v3.0
# ════════════════════════════════════════════════════════════

def calculate(gp: dict, spans: list) -> dict:
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
    log.append(f"Пролётов: {N}  W={W_build:.0f}м  S={S_floor:.0f}м²")

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
    for i, (Hu, Hl, Hf) in enumerate(span_heights):
        log.append(f"Пролёт {i+1}: H_кол={Hf:.2f}м (надкр={Hu:.2f}м подкр={Hl:.2f}м)")
    H_full_max = max(h[2] for h in span_heights)
    S_walls = P_walls * H_full_max

    # 1+2. Прогоны и фермы
    g_links = 0.05
    G_pur_all_t = 0.0; G_tr_m1_all = 0.0; G_tr_m2_all = 0.0
    span_data = []
    for i, sp in enumerate(spans):
        L = sp["L_span"]; tt = sp["truss_type"]; B = sp["B_step"]
        Ss = L_build * L
        Q_load_total = sp["Q_roof"] + sp["Q_purlin"] + Q_snow + Q_dust + Q_tech + g_links
        a_pr = 3.0
        qp_tm = (sp["Q_roof"] + sp["Q_purlin"] + Q_snow + Q_dust + Q_tech) * a_pr * yc / 9.81
        mp, pname = select_purlin(qp_tm, B)
        n_pr = int(L / a_pr) + 1
        g_pur = mp * n_pr / (L * B)
        G_pur_t = g_pur * Ss / 1000
        G_pur_all_t += G_pur_t
        n_tr = L_build / B + 1
        Q_tm = Q_load_total * B * yc / 9.81
        G_tr1 = None
        if tt == "Уголки":
            Gkn = (Q_load_total * B / 1000 + 0.018) * 1.4 * L**2 / 0.85 * yc
            G_tr1 = Gkn / 9.81 * n_tr
            G_tr_m1_all += G_tr1
        G_tr2 = None
        mt = get_truss_mass_m2(tt, L, Q_tm)
        if mt is not None:
            G_tr2 = mt * n_tr
            G_tr_m2_all += G_tr2
        span_data.append({
            "idx": i+1, "L_span": L, "S_span": Ss, "tt": tt, "B_step": B,
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

    # 3. Связи
    G_br_total = 0.0; br_rows = []
    for i, sp in enumerate(spans):
        Ss = L_build * sp["L_span"]
        gbr = get_bracing_kgm2(sp["q_crane_t"], sp["B_step"])
        Gbr = gbr * Ss / 1000
        G_br_total += Gbr
        br_rows.append({"пролёт": i+1, "расход_кгм2": gbr, "масса_т": round(Gbr, 2)})
    res["связи_покрытия"] = {
        "расход_кгм2": round(G_br_total * 1000 / S_floor, 2) if S_floor else 0,
        "масса_общая_т": round(G_br_total, 2),
        "по_пролётам": br_rows,
    }

    # 4. Подстропильные фермы
    G_sub_m1 = 0.0; G_sub_m2 = 0.0; sub_rows = []
    need_sub = any(sp["col_step"] == 12 and sp["B_step"] < sp["col_step"] for sp in spans)
    if need_sub:
        for i, sp in enumerate(spans):
            if not (sp["col_step"] == 12 and sp["B_step"] < sp["col_step"]):
                sub_rows.append({"пролёт": i+1, "G_М1_т": 0, "G_М2_т": "н/п", "R_кн": 0})
                continue
            L = sp["L_span"]; B = sp["B_step"]
            Q_load_sp = span_data[i]["Q_load_total"]
            n_bays = L_build / sp["col_step"]
            R_kn = Q_load_sp * B * yc * L / 2
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

    # 5. Подкрановые балки
    G_pb_m1 = 0.0; G_pb_m2 = 0.0; pb_rows = []

    def _pb_row(sp_obj, is_edge, label):
        nonlocal G_pb_m1, G_pb_m2
        q = sp_obj["q_crane_t"]; nc = sp_obj["n_cranes"]
        wp = sp_obj["with_pass"]; mode = sp_obj["crane_mode"]
        mf_m1 = CRANE_MODE_FACTOR_M1[mode]
        mf_m2 = CRANE_MODE_FACTOR_M2[mode]
        L_pb = float(sp_obj["col_step"])
        n_bays_a = math.ceil(L_build / L_pb)
        alp = _lkp(CRANE_BEAM_ALPHA, q)
        qr  = _lkp(RAIL_WEIGHT_KN, q)
        G1t = (alp * L_pb + qr) * L_pb * 1.4 / 9.81 * mf_m1
        G_pb_m1 += G1t * n_bays_a
        pb_kgm = get_crane_beam_kgm(q, L_pb, nc)
        br_kgm = get_brake_kgm(q, L_pb, nc, wp, is_edge)
        if pb_kgm and br_kgm is not None:
            G_pb_m2 += (pb_kgm + br_kgm) * mf_m2 * L_pb * n_bays_a / 1000
        pb_rows.append({"ряд": label, "G_М1_т": round(G1t * n_bays_a, 2), "q": q})

    _pb_row(spans[0], True, "Крайний Л")
    for mi in range(1, N):
        _pb_row(spans[mi-1], False, f"Средний {mi}Л")
        _pb_row(spans[mi],   False, f"Средний {mi}П")
    _pb_row(spans[N-1], True, "Крайний П")

    res["подкрановые_балки"] = {
        "масса_общая_т_М1": round(G_pb_m1, 2),
        "масса_общая_т_М2": round(G_pb_m2, 2) if G_pb_m2 > 0 else "н/п",
        "ряды_колонн": pb_rows,
    }

    # 6. Колонны
    rho=78.5; pu=1.4; pl=2.1; kMu=0.275; kMl=0.45; gst=0.25; aw=0.15

    def _col_kg(L_sp, q_cr, H_up, H_lo, cs, Q_load_sp):
        L_pb_loc = float(cs)
        Gwu = gst * H_up * (1 - aw) * cs
        Gwl = gst * H_lo * (1 - aw) * cs
        SFv = Q_load_sp * cs * L_sp / 2 + Gwu
        Gcu = SFv * rho * pu * H_up / (kMu * 240000)
        qeq = _lkp(CRANE_Q_EQUIV, q_cr)
        D   = qeq * cs * 1.1 * yc
        alp = _lkp(CRANE_BEAM_ALPHA, q_cr)
        qrr = _lkp(RAIL_WEIGHT_KN, q_cr)
        Gpb = (alp * L_pb_loc + qrr) * L_pb_loc * 1.4
        SFn = SFv + D + Gpb + Gwl + Gcu
        Gcl = SFn * rho * pl * H_lo / (kMl * 240000)
        return (Gcu + Gcl) / 9.81 * 1000

    G_cols_t = 0.0; col_rows_detail = []
    sp0 = spans[0]; H_up0, H_lo0, _ = span_heights[0]
    n_col_0 = round(L_build / sp0["col_step"]) + 1
    Gce = _col_kg(sp0["L_span"], sp0["q_crane_t"], H_up0, H_lo0, sp0["col_step"], span_data[0]["Q_load_total"])
    G_cols_t += Gce * n_col_0 / 1000
    col_rows_detail.append({"ряд": "Крайний Л", "масса_1_кг": round(Gce, 1), "масса_ряд_т": round(Gce * n_col_0 / 1000, 2)})

    for mi in range(1, N):
        sL = spans[mi-1]; sR = spans[mi]
        H_upL, H_loL, _ = span_heights[mi-1]
        cs_mid = sL["col_step"]
        n_col_mid = round(L_build / cs_mid) + 1
        Q_L = span_data[mi-1]["Q_load_total"]; Q_R = span_data[mi]["Q_load_total"]
        Gwu = gst * H_upL * (1 - aw) * cs_mid
        Gwl = gst * H_loL * (1 - aw) * cs_mid
        SFv = (Q_L + Q_R) * cs_mid * (sL["L_span"] + sR["L_span"]) / 4 + Gwu
        Gcu = SFv * rho * pu * H_upL / (kMu * 240000)
        qeqL = _lkp(CRANE_Q_EQUIV, sL["q_crane_t"]); qeqR = _lkp(CRANE_Q_EQUIV, sR["q_crane_t"])
        D = (qeqL + qeqR) * cs_mid * 1.1 * yc
        alpL = _lkp(CRANE_BEAM_ALPHA, sL["q_crane_t"]); qrL = _lkp(RAIL_WEIGHT_KN, sL["q_crane_t"])
        alpR = _lkp(CRANE_BEAM_ALPHA, sR["q_crane_t"]); qrR = _lkp(RAIL_WEIGHT_KN, sR["q_crane_t"])
        Gpb = (alpL * float(sL["col_step"]) + qrL) * float(sL["col_step"]) * 1.4 + \
              (alpR * float(sR["col_step"]) + qrR) * float(sR["col_step"]) * 1.4
        SFn = SFv + D + Gpb + Gwl + Gcu
        Gcl = SFn * rho * pl * H_loL / (kMl * 240000)
        Gcm_kg = (Gcu + Gcl) / 9.81 * 1000
        G_cols_t += Gcm_kg * n_col_mid / 1000
        col_rows_detail.append({"ряд": f"Средний {mi}", "масса_1_кг": round(Gcm_kg, 1), "масса_ряд_т": round(Gcm_kg * n_col_mid / 1000, 2)})

    spN = spans[N-1]; H_upN, H_loN, _ = span_heights[N-1]
    n_col_N = round(L_build / spN["col_step"]) + 1
    Gce2 = _col_kg(spN["L_span"], spN["q_crane_t"], H_upN, H_loN, spN["col_step"], span_data[N-1]["Q_load_total"])
    G_cols_t += Gce2 * n_col_N / 1000
    col_rows_detail.append({"ряд": "Крайний П", "масса_1_кг": round(Gce2, 1), "масса_ряд_т": round(Gce2 * n_col_N / 1000, 2)})

    res["колонны"] = {
        "H_full_м": round(span_heights[0][2], 2),
        "расход_кгм2": round(G_cols_t * 1000 / S_floor, 2) if S_floor else 0,
        "масса_общая_т": round(G_cols_t, 2),
        "по_рядам": col_rows_detail,
        "высоты_пролётов": [{"пролёт":i+1,"H_full":round(h[2],2),"H_upper":round(h[0],2),"H_lower":round(h[1],2)} for i,h in enumerate(span_heights)],
    }

    # 7. Фахверк
    G_fakh_total = 0.0; fakh_rows = []
    for i, sp in enumerate(spans):
        H_full_sp = span_heights[i][2]
        S_walls_sp = P_walls * H_full_sp / N
        gf = get_fakhverk_kgm2(sp["col_step"], sp["has_post"], H_full_sp, sp["rig_load"])
        if gf:
            Gf = gf * S_walls_sp / 1000
            G_fakh_total += Gf
            fakh_rows.append({"пролёт": i+1, "расход_кгм2_стены": gf, "масса_т": round(Gf, 2)})
        else:
            fakh_rows.append({"пролёт": i+1, "ошибка": "н/п", "масса_т": 0})
    res["фахверк"] = {
        "площадь_стен_м2": round(S_walls, 1),
        "масса_общая_т": round(G_fakh_total, 2),
        "по_пролётам": fakh_rows,
    }

    # 8. Ограждение
    res["ограждение"] = {"стены_м2": round(S_walls, 1), "кровля_м2": round(S_floor, 1)}

    # 9. Опоры трубопроводов
    G_pipe_total = 0.0; pipe_rows = []
    for i, sp in enumerate(spans):
        Ss = L_build * sp["L_span"]
        gp2 = get_pipe_support_kgm2(sp["bld_type"])
        Gp = gp2 * Ss / 1000
        G_pipe_total += Gp
        pipe_rows.append({"пролёт": i+1, "расход_кгм2": gp2, "масса_т": round(Gp, 2)})
    res["опоры_трубопроводов"] = {
        "расход_кгм2": round(G_pipe_total * 1000 / S_floor, 2) if S_floor else 0,
        "масса_общая_т": round(G_pipe_total, 2),
        "по_пролётам": pipe_rows,
    }

    # Итого (гибридное суммирование)
    def sv(d, *keys):
        for k in keys:
            v = d.get(k)
            if isinstance(v, (int, float)): return float(v)
        return 0.0

    common = (sv(res["прогоны"],"масса_общая_т") + sv(res["колонны"],"масса_общая_т")
              + sv(res["связи_покрытия"],"масса_общая_т") + sv(res["фахверк"],"масса_общая_т")
              + sv(res["опоры_трубопроводов"],"масса_общая_т"))
    m1_spec = (sv(res["фермы"],"масса_общая_т_М1")
               + sv(res["подстропильные_фермы"],"масса_общая_т_М1")
               + sv(res["подкрановые_балки"],"масса_общая_т_М1"))
    m2_spec = (sv(res["фермы"],"масса_общая_т_М2")
               + sv(res["подстропильные_фермы"],"масса_общая_т_М2")
               + sv(res["подкрановые_балки"],"масса_общая_т_М2"))
    total_m1 = common + m1_spec; total_m2 = common + m2_spec
    res["итого"] = {
        "М1_т":    round(total_m1, 2), "М2_т":    round(total_m2, 2),
        "М1_кгм2": round(total_m1 * 1000 / S_floor, 2) if S_floor else 0,
        "М2_кгм2": round(total_m2 * 1000 / S_floor, 2) if S_floor else 0,
        "min_т":   round(min(total_m1, total_m2), 2),
        "max_т":   round(max(total_m1, total_m2), 2),
        "S_floor": round(S_floor, 1),
    }
    res["_log"] = log
    return res

# ════════════════════════════════════════════════════════════
#  ЭКСПОРТ РЕЗУЛЬТАТОВ
# ════════════════════════════════════════════════════════════

def export_to_file(plain_text: str) -> str:
    """Сохраняет результаты в ~/Documents/ и возвращает путь."""
    docs = os.path.expanduser("~/Documents")
    os.makedirs(docs, exist_ok=True)
    fname = "MetalCalc_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
    path = os.path.join(docs, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(plain_text)
    return path

# ════════════════════════════════════════════════════════════
#  KIVY UI
# ════════════════════════════════════════════════════════════

from kivy.config import Config
Config.set("graphics", "minimum_width",  "360")
Config.set("graphics", "minimum_height", "640")

from kivy.app            import App
from kivy.lang           import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput  import TextInput
from kivy.uix.label      import Label
from kivy.uix.button     import Button
from kivy.uix.spinner    import Spinner
from kivy.uix.checkbox   import CheckBox
from kivy.uix.widget     import Widget
from kivy.metrics        import dp
from kivy.clock          import Clock
from kivy.properties     import StringProperty, BooleanProperty
from kivy.utils          import platform

# Safe-area top padding для iPhone с чёлкой / Dynamic Island
_SAFE_TOP = dp(50) if platform == "ios" else 0
_BLUE     = (0.18, 0.45, 0.8, 1)
_DARK     = (0.13, 0.13, 0.13, 1)
_GRAY     = (0.22, 0.22, 0.22, 1)
_ACCENT   = (0.20, 0.50, 0.90, 1)
_GREEN    = (0.12, 0.60, 0.30, 1)

# Значения полей пролёта по умолчанию
_SPAN_DEFAULTS = dict(
    L_span=24.0, B_step=6, col_step="6", h_rail=8.0, H_col_ov=0.0,
    Q_roof=0.30, Q_purlin=0.25, truss_type="Уголки",
    q_crane_t=50.0, n_cranes="1", with_pass="С проходом",
    crane_mode="Режим 1-6К", rig_load=0.0, has_post=False,
    bld_type="Основные производственные",
)

class Toolbar(BoxLayout):
    title = StringProperty("")
    back  = BooleanProperty(False)

class InputScreen(Screen):
    pass

class ResultScreen(Screen):
    pass

KV = """
#:import dp kivy.metrics.dp

ScreenManager:
    InputScreen:
    ResultScreen:

<Toolbar>:
    size_hint_y: None
    height: dp(50)
    canvas.before:
        Color:
            rgba: 0.18, 0.45, 0.8, 1
        Rectangle:
            pos: self.pos
            size: self.size
    Button:
        text: "<"
        size_hint_x: None
        width: dp(50) if root.back else 0
        opacity: 1 if root.back else 0
        on_release: app.go_back()
        background_color: 0, 0, 0, 0
        bold: True
        font_size: dp(20)
    Label:
        id: toolbar_label
        text: root.title
        bold: True
        font_size: dp(17)
        halign: "left"
        padding_x: dp(8)

<InputScreen>:
    name: "input"
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: 0.13, 0.13, 0.13, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Widget:
            id: safe_top
            size_hint_y: None
            height: 0
        Toolbar:
            id: input_toolbar
        ScrollView:
            BoxLayout:
                id: form
                orientation: "vertical"
                padding: dp(12)
                spacing: dp(6)
                size_hint_y: None
                height: self.minimum_height
        BoxLayout:
            id: bottom_bar
            size_hint_y: None
            height: dp(56)
            padding: dp(8), dp(4)
            spacing: dp(8)
            canvas.before:
                Color:
                    rgba: 0.18, 0.18, 0.18, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                id: calc_btn
                background_color: 0.18, 0.45, 0.8, 1
                bold: True
                font_size: dp(14)
                on_release: app.do_calculate()
            Button:
                id: reset_btn
                size_hint_x: None
                width: dp(90)
                background_color: 0.35, 0.35, 0.35, 1
                on_release: app.do_reset()

<ResultScreen>:
    name: "result"
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: 0.13, 0.13, 0.13, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Widget:
            id: safe_top_r
            size_hint_y: None
            height: 0
        Toolbar:
            id: result_toolbar
            back: True
        ScrollView:
            Label:
                id: result_text
                text: ""
                color: 1, 1, 1, 1
                size_hint_y: None
                height: self.texture_size[1]
                text_size: self.width, None
                padding: dp(12), dp(8)
                markup: True
                font_size: dp(13)
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: dp(8), dp(4)
            spacing: dp(8)
            canvas.before:
                Color:
                    rgba: 0.18, 0.18, 0.18, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                id: save_btn
                background_color: 0.12, 0.60, 0.30, 1
                bold: True
                font_size: dp(14)
                on_release: app.do_save_results()
            Button:
                id: back_btn
                size_hint_x: None
                width: dp(90)
                background_color: 0.35, 0.35, 0.35, 1
                on_release: app.go_back()
"""


class MetalApp(App):

    def build(self):
        try:
            self.title = "MetalCalc"
            root = Builder.load_string(KV)
            self.sm = root
            self._last_result_text = ""  # plain text for export

            inp = root.get_screen("input")
            res = root.get_screen("result")

            # Кириллица — только из Python
            inp.ids.input_toolbar.title = "Металлоёмкость зданий"
            res.ids.result_toolbar.title = "Результаты"
            inp.ids.calc_btn.text  = "РАССЧИТАТЬ"
            inp.ids.reset_btn.text = "СБРОС"
            res.ids.save_btn.text  = "СОХРАНИТЬ В ФАЙЛ"
            res.ids.back_btn.text  = "НАЗАД"

            # Safe area
            inp.ids.safe_top.height  = _SAFE_TOP
            res.ids.safe_top_r.height = _SAFE_TOP

            self._form = inp.ids.form
            self._span_blocks = []   # list of dicts: {key: widget}
            self._build_form()
            return root
        except Exception:
            tb = traceback.format_exc()
            box = BoxLayout(orientation="vertical")
            sv  = ScrollView()
            lbl = Label(
                text="[b][color=ff4444]ОШИБКА:[/color][/b]\n\n" + tb,
                markup=True, size_hint_y=None, font_size="11sp",
                padding=(10, 10), halign="left", valign="top",
            )
            lbl.bind(
                width=lambda *_: lbl.setter("text_size")(lbl, (lbl.width, None)),
                texture_size=lambda *_: lbl.setter("height")(lbl, lbl.texture_size[1]),
            )
            sv.add_widget(lbl); box.add_widget(sv)
            return box

    # ── Виджеты-помощники ────────────────────────────────

    def _section_label(self, title, color="4fc3f7"):
        lbl = Label(
            text=f"[b][color={color}]{title}[/color][/b]",
            markup=True, size_hint_y=None, height=dp(38),
            halign="left", valign="middle", font_size=dp(14),
        )
        lbl.bind(size=lbl.setter("text_size"))
        return lbl

    def _field_widget(self, label, default, input_filter="float"):
        box = BoxLayout(orientation="vertical", size_hint_y=None,
                        height=dp(68), spacing=dp(2))
        lbl = Label(text=label, size_hint_y=None, height=dp(22),
                    halign="left", valign="middle",
                    font_size=dp(12), color=(0.8, 0.8, 0.8, 1))
        lbl.bind(size=lbl.setter("text_size"))
        ti = TextInput(
            text=str(default), multiline=False,
            input_filter=input_filter,
            size_hint_y=None, height=dp(38),
            background_color=_GRAY,
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.4, 0.7, 1, 1),
            font_size=dp(15),
        )
        box.add_widget(lbl); box.add_widget(ti)
        return box, ti

    def _spinner_widget(self, label, values, default):
        box = BoxLayout(orientation="vertical", size_hint_y=None,
                        height=dp(68), spacing=dp(2))
        lbl = Label(text=label, size_hint_y=None, height=dp(22),
                    halign="left", valign="middle",
                    font_size=dp(12), color=(0.8, 0.8, 0.8, 1))
        lbl.bind(size=lbl.setter("text_size"))
        sp = Spinner(text=default, values=values,
                     size_hint=(1, None), height=dp(38),
                     background_color=_BLUE, color=(1, 1, 1, 1),
                     font_size=dp(13))
        box.add_widget(lbl); box.add_widget(sp)
        return box, sp

    def _checkbox_widget(self, label, default=False):
        box = BoxLayout(orientation="horizontal", size_hint_y=None,
                        height=dp(44), spacing=dp(8))
        cb = CheckBox(size_hint=(None, 1), width=dp(44),
                      active=default, color=_BLUE)
        lbl = Label(text=label, halign="left", valign="middle",
                    font_size=dp(13), color=(0.9, 0.9, 0.9, 1))
        lbl.bind(size=lbl.setter("text_size"))
        box.add_widget(cb); box.add_widget(lbl)
        return box, cb

    def _separator(self):
        w = Widget(size_hint_y=None, height=dp(1))
        with w.canvas:
            from kivy.graphics import Color, Rectangle
            Color(0.3, 0.3, 0.3, 1)
            Rectangle(pos=w.pos, size=w.size)
        w.bind(pos=lambda inst, v: setattr(inst.canvas.children[1], 'pos', v),
               size=lambda inst, v: setattr(inst.canvas.children[1], 'size', v))
        return w

    # ── Построение формы ─────────────────────────────────

    def _build_form(self):
        F = self._form
        F.clear_widgets()
        self._span_blocks = []
        self._global_fields = {}

        def s(t, color="4fc3f7"): F.add_widget(self._section_label(t, color))
        def f(d, k, label, default, filt="float"):
            box, ti = self._field_widget(label, default, filt)
            F.add_widget(box); d[k] = ti
        def sp(d, k, label, values, default):
            box, spinner = self._spinner_widget(label, values, default)
            F.add_widget(box); d[k] = spinner

        gf = self._global_fields
        s("Параметры здания")
        f(gf, "L_build", "Длина здания, м", 120)
        f(gf, "Q_snow",  "Снег, кН/м²", 2.1)
        f(gf, "Q_dust",  "Пыль, кН/м²", 0.0)
        f(gf, "Q_tech",  "Тех. нагрузка на кровлю, кН/м²", 0.0)
        f(gf, "yc",      "Коэф. ответственности γc", 1.0)

        # Первый пролёт
        self._add_span_block()

        # Кнопки управления пролётами
        self._btn_container = BoxLayout(size_hint_y=None, height=dp(48),
                                        spacing=dp(8), padding=(0, dp(4)))
        btn_add = Button(text="+ Добавить пролёт", background_color=_ACCENT,
                         font_size=dp(13), bold=True)
        btn_add.bind(on_release=lambda *_: self._add_span_block())
        btn_rem = Button(text="— Убрать пролёт", background_color=(0.45,0.2,0.2,1),
                         font_size=dp(13), size_hint_x=None, width=dp(150))
        btn_rem.bind(on_release=lambda *_: self._remove_span_block())
        self._btn_add = btn_add; self._btn_rem = btn_rem
        self._btn_container.add_widget(btn_add)
        self._btn_container.add_widget(btn_rem)
        F.add_widget(self._btn_container)
        self._update_span_buttons()

    def _add_span_block(self):
        if len(self._span_blocks) >= 6: return
        F = self._form
        idx = len(self._span_blocks) + 1
        d = {}           # input widgets keyed by param name
        added = []       # all top-level widgets added to F for this span

        F.remove_widget(self._btn_container)

        def _add(w): F.add_widget(w); added.append(w); return w
        def s(t, color="4fc3f7"): _add(self._section_label(t, color))
        def f(k, label, default, filt="float"):
            box, ti = self._field_widget(label, default, filt)
            _add(box); d[k] = ti
        def sp(k, label, values, default):
            box, spinner = self._spinner_widget(label, values, default)
            _add(box); d[k] = spinner
        def cb(k, label, default=False):
            box, checkbox = self._checkbox_widget(label, default)
            _add(box); d[k] = checkbox

        s(f"Пролёт {idx}", "80cbc4")
        s("Геометрия пролёта")
        f("L_span",    "Пролёт L, м", 24.0)
        sp("B_step",   "Шаг ферм B, м", ["6", "12"], "6")
        sp("col_step", "Шаг колонн, м", ["6", "12"], "6")
        f("h_rail",    "УГР — уровень головки рельса, м", 8.0)
        f("H_col_ov",  "Высота колонны (0=авто), м", 0.0)

        s("Нагрузки пролёта")
        f("Q_roof",   "Кровля, кН/м²", 0.30)
        f("Q_purlin", "Прогоны, кН/м²", 0.25)

        s("Конструкция")
        sp("truss_type", "Тип ферм", TRUSS_TYPES, "Уголки")
        sp("crane_mode", "Режим крана", CRANE_MODES, "Режим 1-6К")
        f("q_crane_t", "Г/П крана, т", 50.0)
        sp("n_cranes",  "Кол-во кранов", ["1", "2"], "1")
        sp("with_pass", "Тормозные конструкции", ["С проходом", "Без прохода"], "С проходом")

        s("Фахверк")
        f("rig_load",   "Нагрузка на ригель, кг/м", 0.0)
        cb("has_post",  "Стойка фахверка (шаг 12м)")
        sp("bld_type",  "Тип здания (опоры труб)", BLD_TYPES, BLD_TYPES[0])

        d["_widgets_in_F"] = added
        self._span_blocks.append(d)
        F.add_widget(self._btn_container)
        self._update_span_buttons()

    def _remove_span_block(self):
        if len(self._span_blocks) <= 1: return
        F = self._form
        F.remove_widget(self._btn_container)
        d = self._span_blocks.pop()
        for w in d.get("_widgets_in_F", []):
            if w.parent:
                w.parent.remove_widget(w)
        F.add_widget(self._btn_container)
        self._update_span_buttons()

    def _update_span_buttons(self):
        n = len(self._span_blocks)
        self._btn_rem.disabled = (n <= 1)
        self._btn_add.disabled = (n >= 6)

    # ── Чтение параметров ────────────────────────────────

    def _get_float(self, widget, default=0.0):
        if isinstance(widget, TextInput):
            try: return float(widget.text.replace(",", "."))
            except: return default
        return default

    def _get_text(self, widget, default=""):
        if isinstance(widget, Spinner): return widget.text
        if isinstance(widget, TextInput): return widget.text
        return default

    def _get_bool(self, widget):
        if isinstance(widget, CheckBox): return widget.active
        return False

    def _read_params(self):
        gf = self._global_fields
        gp = {
            "L_build": self._get_float(gf.get("L_build"), 120),
            "Q_snow":  self._get_float(gf.get("Q_snow"),  2.1),
            "Q_dust":  self._get_float(gf.get("Q_dust"),  0.0),
            "Q_tech":  self._get_float(gf.get("Q_tech"),  0.0),
            "yc":      self._get_float(gf.get("yc"),      1.0),
        }
        spans = []
        for d in self._span_blocks:
            cs = int(self._get_text(d.get("col_step"), "6"))
            spans.append({
                "L_span":     self._get_float(d.get("L_span"),    24.0),
                "B_step":     int(self._get_text(d.get("B_step"), "6")),
                "col_step":   cs,
                "h_rail":     self._get_float(d.get("h_rail"),    8.0),
                "H_col_ov":   self._get_float(d.get("H_col_ov"), 0.0),
                "Q_roof":     self._get_float(d.get("Q_roof"),    0.30),
                "Q_purlin":   self._get_float(d.get("Q_purlin"),  0.25),
                "truss_type": self._get_text(d.get("truss_type"), "Уголки"),
                "crane_mode": self._get_text(d.get("crane_mode"), "Режим 1-6К"),
                "q_crane_t":  self._get_float(d.get("q_crane_t"), 50.0),
                "n_cranes":   int(self._get_text(d.get("n_cranes"), "1")),
                "with_pass":  self._get_text(d.get("with_pass"), "С проходом") == "С проходом",
                "rig_load":   self._get_float(d.get("rig_load"),  0.0),
                "has_post":   self._get_bool(d.get("has_post")) and cs == 12,
                "bld_type":   self._get_text(d.get("bld_type"),  BLD_TYPES[0]),
            })
        return gp, spans

    # ── Навигация и действия ─────────────────────────────

    def go_back(self):
        self.sm.current = "input"

    def do_reset(self):
        self._build_form()

    def do_calculate(self):
        Clock.schedule_once(self._run_calc, 0.05)

    def _run_calc(self, dt):
        try:
            gp, spans = self._read_params()
            res = calculate(gp, spans)
            txt_markup, txt_plain = self._format_results(res, gp, spans)
            self._last_result_text = txt_plain
            screen = self.sm.get_screen("result")
            screen.ids.result_text.text = txt_markup
            self.sm.current = "result"
        except Exception:
            tb = traceback.format_exc()
            screen = self.sm.get_screen("result")
            screen.ids.result_text.text = "[color=ff6666]ОШИБКА:[/color]\n" + tb
            self.sm.current = "result"

    def do_save_results(self):
        if not self._last_result_text:
            return
        try:
            path = export_to_file(self._last_result_text)
            screen = self.sm.get_screen("result")
            short = os.path.basename(path)
            # Append save notification
            screen.ids.result_text.text += (
                f"\n\n[color=88ff88]Сохранено: {short}[/color]"
            )
        except Exception as e:
            screen = self.sm.get_screen("result")
            screen.ids.result_text.text += f"\n\n[color=ff6666]Ошибка сохранения: {e}[/color]"

    # ── Форматирование результатов ────────────────────────

    def _format_results(self, res, gp, spans):
        """Возвращает (markup_str, plain_str)."""
        SEP  = "─" * 40
        lines_m = []  # markup
        lines_p = []  # plain

        def h(t):
            lines_m.append(f"\n[b][color=4fc3f7]{t}[/color][/b]\n{SEP}")
            lines_p.append(f"\n{t}\n{SEP}")

        def r(label, val):
            lines_m.append(f"  {label:<30}{val}")
            lines_p.append(f"  {label:<30}{val}")

        it = res["итого"]
        N  = len(spans)
        now = datetime.now().strftime("%d.%m.%Y %H:%M")

        # Шапка
        lines_m.append(f"[b][size=16]МЕТАЛЛОЁМКОСТЬ ЗДАНИЙ[/size][/b]")
        lines_p.append("МЕТАЛЛОЁМКОСТЬ ЗДАНИЙ")
        lines_m.append(f"[color=aaaaaa]{now}  Пролётов: {N}[/color]")
        lines_p.append(f"{now}  Пролётов: {N}")
        lines_m.append(SEP)
        lines_p.append(SEP)

        lines_m.append(f"[b][color=ffdd44]ИТОГО М1:  {it['М1_т']} т  ({it['М1_кгм2']} кг/м²)[/color][/b]")
        lines_m.append(f"[b][color=ffdd44]ИТОГО М2:  {it['М2_т']} т  ({it['М2_кгм2']} кг/м²)[/color][/b]")
        lines_m.append(f"[b]ДИАПАЗОН:  {it['min_т']} — {it['max_т']} т[/b]")
        lines_m.append(f"[color=aaaaaa]Площадь пола: {it['S_floor']} м²[/color]")
        lines_p.append(f"ИТОГО М1:  {it['М1_т']} т  ({it['М1_кгм2']} кг/м²)")
        lines_p.append(f"ИТОГО М2:  {it['М2_т']} т  ({it['М2_кгм2']} кг/м²)")
        lines_p.append(f"ДИАПАЗОН:  {it['min_т']} — {it['max_т']} т")
        lines_p.append(f"Площадь пола: {it['S_floor']} м²")

        h("1. ПРОГОНЫ [М1]")
        r("Масса, т:", res["прогоны"]["масса_общая_т"])
        for row in res["прогоны"]["по_пролётам"]:
            r(f"  Пролёт {row['пролёт']} ({row['профиль']}):", f"{row['масса_т']} т  ({row['расход_кгм2']} кг/м²)")

        h("2. СТРОПИЛЬНЫЕ ФЕРМЫ")
        r("Масса М1, т:", res["фермы"]["масса_общая_т_М1"])
        r("Масса М2, т:", res["фермы"]["масса_общая_т_М2"])
        for row in res["фермы"]["по_пролётам"]:
            r(f"  Пролёт {row['пролёт']}:", f"М1={row['G_М1_т']} М2={row['G_М2_т']} т")

        h("3. СВЯЗИ ПОКРЫТИЯ [М2]")
        r("Масса, т:", res["связи_покрытия"]["масса_общая_т"])
        r("Расход, кг/м²:", res["связи_покрытия"]["расход_кгм2"])

        h("4. ПОДСТРОПИЛЬНЫЕ ФЕРМЫ")
        psf = res["подстропильные_фермы"]
        if "примечание" in psf:
            lines_m.append(f"  {psf['примечание']}")
            lines_p.append(f"  {psf['примечание']}")
        else:
            r("Масса М1, т:", psf.get("масса_общая_т_М1", "н/п"))
            r("Масса М2, т:", psf.get("масса_общая_т_М2", "н/п"))

        h("5. ПОДКРАНОВЫЕ БАЛКИ")
        pb = res["подкрановые_балки"]
        r("Масса М1, т:", pb["масса_общая_т_М1"])
        r("Масса М2, т:", pb["масса_общая_т_М2"])
        for row in pb["ряды_колонн"]:
            r(f"  {row['ряд']} (Q={row['q']}т):", f"{row['G_М1_т']} т")

        h("6. КОЛОННЫ [М1]")
        kl = res["колонны"]
        r("Масса, т:", kl["масса_общая_т"])
        r("Расход, кг/м²:", kl["расход_кгм2"])
        for h_row in kl.get("высоты_пролётов", []):
            r(f"  Пролёт {h_row['пролёт']} H_кол:", f"{h_row['H_full']} м")
        for c_row in kl["по_рядам"]:
            r(f"  {c_row['ряд']}:", f"1 кол.={c_row['масса_1_кг']} кг  ряд={c_row['масса_ряд_т']} т")

        h("7. ФАХВЕРК [М2]")
        fh = res["фахверк"]
        r("Масса, т:", fh["масса_общая_т"])
        r("Площадь стен, м²:", fh["площадь_стен_м2"])

        h("8. ОГРАЖДЕНИЕ (справочно)")
        og = res["ограждение"]
        r("Стены, м²:", og["стены_м2"])
        r("Кровля, м²:", og["кровля_м2"])

        h("9. ОПОРЫ ТРУБОПРОВОДОВ [М2]")
        op = res["опоры_трубопроводов"]
        r("Масса, т:", op["масса_общая_т"])
        r("Расход, кг/м²:", op["расход_кгм2"])

        h("ПАРАМЕТРЫ РАСЧЁТА")
        r("Длина здания, м:", gp["L_build"])
        r("Q_снег, кН/м²:", gp["Q_snow"])
        r("γc:", gp["yc"])
        for i, sp in enumerate(spans):
            lines_m.append(f"  [color=80cbc4]Пролёт {i+1}:[/color] L={sp['L_span']}м B={sp['B_step']}м  кран={sp['q_crane_t']}т {sp['crane_mode']}")
            lines_p.append(f"  Пролёт {i+1}: L={sp['L_span']}м B={sp['B_step']}м  кран={sp['q_crane_t']}т {sp['crane_mode']}")

        return "\n".join(lines_m), "\n".join(lines_p)


if __name__ == "__main__":
    MetalApp().run()
