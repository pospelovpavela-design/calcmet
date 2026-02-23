#!/usr/bin/env python3
"""
Металлоёмкость производственных зданий — Android-версия на Kivy/KivyMD
Все таблицы вшиты в код, внешние файлы не требуются.
"""
import os
import sys
import math
import traceback

# ── Запись краша в файл (читать через менеджер файлов: Загрузки/metalcalc_crash.log) ──
def _save_crash(exc_type, exc_value, exc_tb):
    text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    for path in [
        "/sdcard/Download/metalcalc_crash.log",
        "/storage/emulated/0/Download/metalcalc_crash.log",
        os.path.join(os.path.expanduser("~"), "metalcalc_crash.log"),
    ]:
        try:
            with open(path, "w") as f:
                f.write(text)
            break
        except Exception:
            continue
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = _save_crash

# ─────────────────────────────────────────────────────────
#  HARDCODED ДАННЫЕ (Метод 1)
# ─────────────────────────────────────────────────────────
PURLIN_TABLE = [
    (0.45, 110.4, 220.8,  "Швеллер 20"),
    (0.65, 126.0, 252.0,  "Швеллер 22"),
    (0.90, 144.0, 288.0,  "Швеллер 24"),
    (1.25, 166.2, 332.4,  "Швеллер 27"),
    (1.70, 190.8, 381.6,  "Швеллер 30"),
    (2.50, 220.8, 441.6,  "2×Швеллер 20"),
]
CRANE_BEAM_ALPHA = {5:0.08,10:0.09,20:0.12,32:0.15,50:0.18,
                    80:0.22,100:0.26,125:0.30,200:0.36,320:0.40,400:0.45}
RAIL_WEIGHT_KN   = {5:0.461,10:0.461,20:0.461,32:0.598,50:0.598,
                    80:0.831,100:1.135,125:1.135,200:1.135,320:1.417,400:1.417}
CRANE_Q_EQUIV    = {5:8,10:12,20:20,32:28,50:38,80:55,
                    100:68,125:80,200:105,320:145,400:175}
BEAM_HEIGHT_RATIO = {20:(1/7,1/9),32:(1/7,1/9),50:(1/6,1/8.5),
                     80:(1/6,1/7.5),100:(1/6,1/7),125:(1/6,1/7)}

# ─────────────────────────────────────────────────────────
#  HARDCODED ТАБЛИЦЫ (Метод 2)
# ─────────────────────────────────────────────────────────
TRUSS_LOADS = [2.0,2.5,3.0,3.5,4.0,4.5,5.0,5.5,6.0,
               6.5,7.0,7.5,8.0,8.5,9.0,9.5,10.0,10.5,
               11.0,11.5,12.0,12.5]
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
_CB_Q1=[5,10,20,32,50]; _CB_Q2=[80,100,125,200,400]
CRANE_BEAM_T1={6:[80,85,90,190,200,100,240,250,105,140],12:[150,160,320,350,180,200,390,440,220,470]}
CRANE_BEAM_T2={12:[290,320,380,940,980,300,330,500,350,540],18:[460,480,500,1020,1080,490,520,540,1120,1180],24:[680,720,780,1040,1120,820,920,1620,1840,880]}
BRAKE_T1={(6,True,True):[100,110],(6,True,False):[65,70],(6,False,True):[120,140],(6,False,False):[70,75],
          (12,True,True):[100,120],(12,True,False):[65,70],(12,False,True):[100,120],(12,False,False):[70,75]}
BRAKE_T2={(12,True,True):[120,140],(12,True,False):[80,100],(12,False,True):[140,160],(12,False,False):[60,80],
          (18,True,True):[120,140],(18,True,False):[80,100],(18,False,True):[140,160],(18,False,False):[80,100],
          (24,True,True):[220,240],(24,True,False):[140,160],(24,False,True):[220,240],(24,False,False):[140,160]}

# ─────────────────────────────────────────────────────────
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ─────────────────────────────────────────────────────────
def _lookup(d, val):
    for k in sorted(d):
        if val <= k: return d[k]
    return d[sorted(d)[-1]]

def select_purlin(load_tm, span_m):
    for max_l, m6, m12, name in PURLIN_TABLE:
        if load_tm <= max_l:
            return (m6 if span_m <= 6 else m12), name
    _, m6, m12, name = PURLIN_TABLE[-1]
    return (m6 if span_m <= 6 else m12), name

def interp_table(loads, masses, target):
    for i, ld in enumerate(loads):
        if target <= ld: return masses[i]
    return masses[-1]

def ceil_to_table(target, values):
    for v in sorted(values):
        if target <= v: return v
    return sorted(values)[-1]

def get_truss_mass(truss_type, span_m, load_tm):
    spans = sorted(TRUSS_MASSES.get(truss_type, {}).keys())
    if not spans: return None
    span_key = ceil_to_table(span_m, spans)
    masses = TRUSS_MASSES[truss_type].get(span_key)
    if masses is None: return None
    return interp_table(TRUSS_LOADS, masses, load_tm)

def get_subtruss_mass(R_t):
    R_ceil = ceil_to_table(R_t, SUBTRUSS_LOADS)
    return interp_table(SUBTRUSS_LOADS, SUBTRUSS_MASSES, R_ceil)

def get_bracing(q_t, bstep):
    if q_t <= 120: return 15.0 if bstep <= 6 else 35.0
    return 40.0 if bstep <= 6 else 55.0

def get_crane_beam_kgm(q_t, span_m, n_cranes):
    try:
        if q_t <= 50: table, q_ord = CRANE_BEAM_T1, _CB_Q1
        else:         table, q_ord = CRANE_BEAM_T2, _CB_Q2
        spans = sorted(table.keys())
        span_key = ceil_to_table(span_m, spans)
        vals = table.get(span_key)
        if vals is None: return None
        qi = min(range(len(q_ord)), key=lambda i: abs(q_ord[i]-q_t))
        ci = qi*2 + (0 if n_cranes==1 else 1)
        return vals[ci] if ci < len(vals) else None
    except: return None

def get_brake_kgm(q_t, span_m, n_cranes, with_pass, is_edge):
    try:
        table = BRAKE_T1 if q_t<=50 else BRAKE_T2
        spans = sorted({k[0] for k in table})
        span_key = ceil_to_table(span_m, spans)
        vals = table.get((span_key, is_edge, with_pass))
        if vals is None:
            vals = next((v for k,v in table.items() if k[0]==span_key), None)
        if vals:
            return vals[0 if n_cranes==1 else min(1,len(vals)-1)]
    except: pass
    return None

def get_fakhverk_kgm2(step_col, has_post, h_bld, rig_load):
    try:
        if step_col<=6 and has_post: ft='III'
        elif step_col<=6: ft='I'
        else: ft='II'
        lc = 0 if rig_load<=0 else (1 if rig_load<=100 else 2)
        hc = 0 if h_bld<=10 else (1 if h_bld<=20 else 2)
        return FAKHVERK_DATA.get((ft, lc, hc))
    except: return None

def calculate(params):
    L_build=params["L_build"]; W_build=params["W_build"]
    L_span=params["L_span"];   B_step=params["B_step"]
    col_step=params["col_step"]; h_rail=params["h_rail"]
    Q_snow=params["Q_snow"];   Q_dust=params["Q_dust"]
    Q_roof=params["Q_roof"];   Q_purlin=params["Q_purlin"]
    yc=params["yc"];           truss_type=params["truss_type"]
    q_crane_t=params["q_crane_t"]; n_cranes=params["n_cranes"]
    with_pass=params["with_pass"]; rig_load=params["rig_load"]
    has_post=params["has_post"]; bld_type=params["bld_type"]

    res={}
    S_floor=L_build*W_build; P_walls=2*(L_build+W_build)
    H_lower=h_rail

    # 1. ПРОГОНЫ
    step_p=3.0
    q_pr_tm=(Q_roof+Q_purlin+Q_snow+Q_dust)*step_p*yc/9.81
    mass_p, p_name=select_purlin(q_pr_tm, B_step)
    n_pr=L_span/step_p+3
    g_pur=mass_p*n_pr/(L_span*B_step)
    res["прогоны"]=dict(профиль=p_name, нагрузка_тм=round(q_pr_tm,3),
        расход_кгм2=round(g_pur,2), масса_т=round(g_pur*S_floor/1000,2))

    # 2. ФЕРМЫ
    g_links=0.05; gn=Q_snow+Q_dust+Q_roof+Q_purlin+g_links
    Q_tm=(gn*B_step*yc)/9.81
    g_m1=None
    if truss_type=="Уголки":
        G_kn=(gn*B_step/1000+0.018)*1.4*L_span**2/0.85*yc
        G_t=G_kn/9.81
        n_tr=L_build/B_step+1
        g_m1=round(G_t*1000*n_tr/S_floor,2)
    mtr=get_truss_mass(truss_type,L_span,Q_tm)
    g_m2=None
    if mtr is not None:
        n_tr=L_build/B_step+1
        g_m2=round(mtr*1000*n_tr/S_floor,2)
    res["фермы"]=dict(нагрузка_тм=round(Q_tm,3),М1=g_m1 or "н/п",М2=g_m2 or "н/п",
        масса_т_М2=round(g_m2*S_floor/1000,2) if g_m2 else "н/п")

    # 3. СВЯЗИ
    g_br=get_bracing(q_crane_t,B_step)
    res["связи"]=dict(расход_кгм2=g_br, масса_т=round(g_br*S_floor/1000,2))

    # 4. ПОДСТРОПИЛЬНЫЕ ФЕРМЫ
    if col_step==12 and B_step<col_step:
        R_kn=Q_tm*9.81*L_span/2; R_t=R_kn/9.81
        Rf=max(100,min(R_kn,400)); a=(Rf-100)*0.0002+0.044
        G_pf_t=a*144
        n_sub=(L_build/col_step)*(max(0,round(W_build/L_span)-1))
        if n_sub<=0: n_sub=L_build/col_step
        g_s1=round(G_pf_t*1000*n_sub/S_floor,2)
        ms=get_subtruss_mass(R_t)
        g_s2=round(ms*1000*n_sub/S_floor,2) if ms else "н/п"
        res["подстроп"]=dict(R_кн=round(R_kn,1),М1=g_s1,М2=g_s2)
    else:
        res["подстроп"]=dict(примечание="Не требуются")

    # 5. ПОДКРАНОВЫЕ БАЛКИ
    a_pb=_lookup(CRANE_BEAM_ALPHA,q_crane_t)
    qr=_lookup(RAIL_WEIGHT_KN,q_crane_t); L_pb=float(col_step)
    G_pb_kn=(a_pb*L_pb+qr)*L_pb*1.4
    G_pb_t=G_pb_kn/9.81
    n_along=math.ceil(L_build/col_step)
    n_edge=2; n_mid=max(0,round(W_build/L_span)-1)
    g_pb_m1=round(G_pb_t*1000*(n_edge+n_mid*2)*n_along/S_floor,2)
    pb_e=get_crane_beam_kgm(q_crane_t,L_pb,n_cranes)
    br_e=get_brake_kgm(q_crane_t,L_pb,n_cranes,with_pass,True)
    pb_m=get_crane_beam_kgm(q_crane_t,L_pb,n_cranes)
    br_m=get_brake_kgm(q_crane_t,L_pb,n_cranes,with_pass,False)
    g_pb_m2="н/п"
    if pb_e and br_e is not None:
        G_e=(pb_e+(br_e or 0))*L_pb*n_along*n_edge/1000
        G_m=((pb_m or 0)+(br_m or 0))*L_pb*n_along*n_mid/1000
        g_pb_m2=round((G_e+G_m)*1000/S_floor,2)
    res["подкрановые"]=dict(G_1пб_т=round(G_pb_t,2),
        М1=g_pb_m1, М2=g_pb_m2, балка_кгм=pb_e, тормоз_кгм=br_e)

    # 6. КОЛОННЫ
    rho=78.5; pu=1.4; pl=2.1; kmu=0.275; kml=0.45
    hbr=BEAM_HEIGHT_RATIO.get(
        min(BEAM_HEIGHT_RATIO,key=lambda k:abs(k-q_crane_t)),(1/7,1/9))
    h_pb_beam=L_pb*(hbr[0] if col_step<=6 else hbr[1])
    H_upper=max(1.5,h_pb_beam+0.12+0.3)
    H_full=H_upper+H_lower
    S_walls=P_walls*H_full
    gst=0.25; aw=0.15
    Gw_up=gst*H_upper*(1-aw)*col_step
    Gw_lo=gst*H_lower*(1-aw)*col_step
    SFv=(Q_roof+Q_purlin+Q_snow+Q_dust)*col_step*L_span/2+Gw_up
    Gcu=SFv*rho*pu*H_upper/(kmu*24000)
    qeq=_lookup(CRANE_Q_EQUIV,q_crane_t)
    D=qeq*col_step*1.1*yc
    SFn=SFv+D+G_pb_kn+Gw_lo+Gcu
    Gcl=SFn*rho*pl*H_lower/(kml*24000)
    Gc_kg=(Gcu+Gcl)/9.81*1000
    nc=(round(L_build/col_step)+1)*(round(W_build/L_span)+1)
    g_col=round(Gc_kg*nc/S_floor,2)
    res["колонны"]=dict(n=nc,ΣFv=round(SFv,1),ΣFn=round(SFn,1),
        масса_1_кг=round(Gc_kg,1), расход_кгм2=g_col,
        масса_т=round(Gc_kg*nc/1000,2))

    # 7. ФАХВЕРК
    gf=get_fakhverk_kgm2(col_step,has_post,H_full,rig_load)
    if gf:
        res["фахверк"]=dict(расход_кгм2_стен=gf, масса_т=round(gf*S_walls/1000,2))
    else:
        res["фахверк"]=dict(расход_кгм2_стен="н/п",масса_т="н/п")

    # 8. ОГРАЖДЕНИЕ
    res["ограждение"]=dict(стены_м2=round(S_walls,1),кровля_м2=round(S_floor,1))

    # 9. ОПОРЫ
    pipe_map={"Основные производственные":(11,22),
              "Здания энергоносителей":(23,40),"Вспомогательные здания":(2,4)}
    rng=pipe_map.get(bld_type,(11,22))
    gp=(rng[0]+rng[1])/2
    res["опоры"]=dict(расход_кгм2=gp, масса_т=round(gp*S_floor/1000,2))

    def sf(d,*ks):
        for k in ks:
            v=d.get(k)
            if isinstance(v,(int,float)): return v
        return 0.0

    tm1=(sf(res["прогоны"],"масса_т")+sf(res["фермы"],"масса_т_М2")
         +sf(res.get("подстроп",{}),"М1")*S_floor/1000
         +sf(res["подкрановые"],"G_1пб_т")*(n_edge+n_mid*2)*n_along
         +sf(res["колонны"],"масса_т"))
    tm2=(sf(res["прогоны"],"масса_т")+sf(res["фермы"],"масса_т_М2")
         +sf(res["связи"],"масса_т")
         +sf(res.get("подстроп",{}),"М2")*S_floor/1000
         +sf(res["подкрановые"],"М2")*S_floor/1000
         +sf(res["колонны"],"масса_т")
         +sf(res["фахверк"],"масса_т")
         +sf(res["опоры"],"масса_т"))
    res["итого"]=dict(
        М1_т=round(tm1,2), М2_т=round(tm2,2),
        М1_кгм2=round(tm1*1000/S_floor,2),
        М2_кгм2=round(tm2*1000/S_floor,2))
    return res


# ─────────────────────────────────────────────────────────
#  KIVY UI  (чистый Kivy, без KivyMD)
# ─────────────────────────────────────────────────────────
from kivy.config import Config
Config.set("graphics", "minimum_width", "360")
Config.set("graphics", "minimum_height", "640")

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty

_BLUE  = (0.18, 0.45, 0.8, 1)
_DARK  = (0.13, 0.13, 0.13, 1)
_GRAY  = (0.25, 0.25, 0.25, 1)


class _Toolbar(BoxLayout):
    title = StringProperty("")
    back  = BooleanProperty(False)


KV = """
#:import dp kivy.metrics.dp

ScreenManager:
    InputScreen:
    ResultScreen:

<_Toolbar>:
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
        _Toolbar:
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
            size_hint_y: None
            height: dp(54)
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
                on_release: app.do_calculate()
                background_color: 0.18, 0.45, 0.8, 1
                bold: True
                font_size: dp(14)
            Button:
                id: reset_btn
                on_release: app.do_reset()
                size_hint_x: None
                width: dp(100)
                background_color: 0.35, 0.35, 0.35, 1

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
        _Toolbar:
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
"""


class InputScreen(Screen):
    pass


class ResultScreen(Screen):
    pass


class MetalApp(App):

    def build(self):
        try:
            self.title = "Металлоёмкость зданий v1.0"
            root = Builder.load_string(KV)
            self.sm = root
            # Кириллицу выставляем из Python — KV-парсер не поддерживает
            # non-ASCII строки в property-значениях (SyntaxError)
            inp = root.get_screen("input")
            res = root.get_screen("result")
            inp.ids.input_toolbar.title = "Металлоёмкость зданий"
            res.ids.result_toolbar.title = "Результаты"
            inp.ids.calc_btn.text = "РАССЧИТАТЬ"
            inp.ids.reset_btn.text = "СБРОС"
            self._build_form(inp.ids.form)
            return root
        except Exception:
            tb = traceback.format_exc()
            # Показать ошибку прямо на экране
            box = BoxLayout(orientation="vertical")
            sv = ScrollView()
            lbl = Label(
                text="[b][color=ff4444]ОШИБКА ЗАПУСКА:[/color][/b]\n\n" + tb,
                markup=True,
                size_hint_y=None,
                font_size="11sp",
                padding=(10, 10),
                halign="left",
                valign="top",
            )
            lbl.bind(
                width=lambda *_: lbl.setter("text_size")(lbl, (lbl.width, None)),
                texture_size=lambda *_: lbl.setter("height")(lbl, lbl.texture_size[1]),
            )
            sv.add_widget(lbl)
            box.add_widget(sv)
            return box

    # ── Вспомогательные виджеты ──────────────────────────

    def _section(self, title):
        lbl = Label(
            text=f"[b][color=4fc3f7]{title}[/color][/b]",
            markup=True,
            size_hint_y=None, height=dp(38),
            halign="left", valign="middle",
            font_size=dp(14),
        )
        lbl.bind(size=lbl.setter("text_size"))
        return lbl

    def _field(self, label, default):
        box = BoxLayout(orientation="vertical", size_hint_y=None,
                        height=dp(68), spacing=dp(2))
        lbl = Label(text=label, size_hint_y=None, height=dp(22),
                    halign="left", valign="middle",
                    font_size=dp(12), color=(0.8, 0.8, 0.8, 1))
        lbl.bind(size=lbl.setter("text_size"))
        ti = TextInput(
            text=str(default),
            multiline=False,
            input_filter="float",
            size_hint_y=None, height=dp(38),
            background_color=(0.22, 0.22, 0.22, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.4, 0.7, 1, 1),
            font_size=dp(15),
        )
        box.add_widget(lbl)
        box.add_widget(ti)
        return box, ti

    def _spinner_row(self, label, values, default):
        box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(68),
                        spacing=dp(2))
        lbl = Label(text=label, size_hint_y=None, height=dp(22),
                    halign="left", valign="middle",
                    font_size=dp(12), color=(0.8, 0.8, 0.8, 1))
        lbl.bind(size=lbl.setter("text_size"))
        sp = Spinner(text=default, values=values,
                     size_hint=(1, None), height=dp(38),
                     background_color=_BLUE, color=(1, 1, 1, 1),
                     font_size=dp(14))
        box.add_widget(lbl)
        box.add_widget(sp)
        return box, sp

    def _checkbox_row(self, label):
        box = BoxLayout(orientation="horizontal", size_hint_y=None,
                        height=dp(44), spacing=dp(8))
        cb = CheckBox(size_hint=(None, 1), width=dp(44),
                      color=_BLUE)
        lbl = Label(text=label, halign="left", valign="middle",
                    font_size=dp(13), color=(0.9, 0.9, 0.9, 1))
        lbl.bind(size=lbl.setter("text_size"))
        box.add_widget(cb)
        box.add_widget(lbl)
        return box, cb

    def _build_form(self, form):
        F = form
        fields = {}
        def s(t):  F.add_widget(self._section(t))
        def f(k, label, default):
            box, ti = self._field(label, default)
            F.add_widget(box); fields[k] = ti
        def sp(k, label, values, default):
            box, spinner = self._spinner_row(label, values, default)
            F.add_widget(box); fields[k] = spinner
        def cb(k, label):
            box, checkbox = self._checkbox_row(label)
            F.add_widget(box); fields[k] = checkbox

        s("Геометрия здания")
        f("L_build", "Длина здания по осям, м", 120)
        f("W_build", "Ширина здания, м", 48)
        f("L_span",  "Пролёт фермы L, м", 24)
        f("B_step",  "Шаг ферм B, м", 6)
        sp("col_step", "Шаг колонн, м", ["6", "12"], "12")
        f("h_rail",  "Уровень головки рельса, м", 8.0)

        s("Нагрузки (расчётные, кН/м²)")
        f("Q_snow",   "Снег (Qснег)", 2.1)
        f("Q_dust",   "Пыль (Qпыль)", 0.0)
        f("Q_roof",   "Кровля (Qкровля)", 0.65)
        f("Q_purlin", "Вес прогона (Qвес.прог.)", 0.35)
        f("yc",       "Коэф. ответственности γc", 1.0)

        s("Стропильные фермы")
        sp("truss_type", "Тип фермы", ["Уголки", "Двутавры", "Молодечно"], "Уголки")

        s("Мостовой кран")
        f("q_crane_t", "Грузоподъёмность крана, т", 50)
        sp("n_cranes", "Кол-во кранов в пролёте", ["1", "2"], "1")
        sp("with_pass", "Тормозные пути",
           ["С проходом", "Без прохода"], "С проходом")

        s("Фахверк")
        f("rig_load", "Нагрузка на ригели, кг/м.п.", 0)
        cb("has_post", "Наличие стойки фахверка (шаг 12 м)")

        s("Тип здания (опоры трубопроводов)")
        sp("bld_type", "Тип здания",
           ["Основные производственные",
            "Здания энергоносителей",
            "Вспомогательные здания"],
           "Основные производственные")

        self._fields = fields

    # ── Считать параметры из формы ───────────────────────

    def _get(self, key, default=0.0):
        w = self._fields.get(key)
        if w is None: return default
        if isinstance(w, TextInput):
            try: return float(w.text.replace(",", "."))
            except: return default
        if isinstance(w, Spinner):
            return w.text
        if isinstance(w, CheckBox):
            return w.active
        return default

    def _read_params(self):
        col_step = int(self._get("col_step", "12"))
        return {
            "L_build":    self._get("L_build", 120),
            "W_build":    self._get("W_build", 48),
            "L_span":     self._get("L_span",  24),
            "B_step":     self._get("B_step",  6),
            "col_step":   col_step,
            "h_rail":     self._get("h_rail",  8),
            "Q_snow":     self._get("Q_snow",  2.1),
            "Q_dust":     self._get("Q_dust",  0),
            "Q_roof":     self._get("Q_roof",  0.65),
            "Q_purlin":   self._get("Q_purlin", 0.35),
            "yc":         self._get("yc",       1.0),
            "truss_type": self._get("truss_type", "Уголки"),
            "q_crane_t":  self._get("q_crane_t", 50),
            "n_cranes":   int(self._get("n_cranes", "1")),
            "with_pass":  self._get("with_pass", "С проходом") == "С проходом",
            "rig_load":   self._get("rig_load", 0),
            "has_post":   bool(self._get("has_post")) and col_step == 12,
            "bld_type":   self._get("bld_type", "Основные производственные"),
        }

    # ── Навигация и действия ─────────────────────────────

    def go_back(self):
        self.sm.current = "input"

    def do_reset(self):
        self.sm.current = "input"

    def do_calculate(self):
        Clock.schedule_once(self._run_calc, 0.1)

    def _run_calc(self, dt):
        try:
            params = self._read_params()
            res = calculate(params)
            self._show_results(res)
        except Exception:
            tb = traceback.format_exc()
            screen = self.sm.get_screen("result")
            screen.ids.result_text.text = (
                "[color=ff6666]ОШИБКА РАСЧЁТА:[/color]\n" + tb
            )
            self.sm.current = "result"

    def _show_results(self, res):
        lines = []
        S = "─" * 38

        def h(t): lines.append(f"\n[b][color=4fc3f7]{t}[/color][/b]\n{S}")
        def r(label, val): lines.append(f"  {label:<28}{val}")

        it = res["итого"]
        lines.append(f"[b][size=16]РЕЗУЛЬТАТЫ[/size][/b]")
        lines.append(S)
        lines.append(f"[b]ИТОГО М1:[/b]  {it['М1_т']} т  ({it['М1_кгм2']} кг/м²)")
        lines.append(f"[b]ИТОГО М2:[/b]  {it['М2_т']} т  ({it['М2_кгм2']} кг/м²)")

        h("1. ПРОГОНЫ [М1]")
        pr = res["прогоны"]
        r("Профиль:", pr["профиль"])
        r("Нагрузка, т/м:", pr["нагрузка_тм"])
        r("Расход, кг/м²:", pr["расход_кгм2"])
        r("Масса, т:", pr["масса_т"])

        h("2. СТРОПИЛЬНЫЕ ФЕРМЫ")
        fm = res["фермы"]
        r("Нагрузка, т/м:", fm["нагрузка_тм"])
        r("Расход М1, кг/м²:", fm["М1"])
        r("Расход М2, кг/м²:", fm["М2"])

        h("3. СВЯЗИ ПОКРЫТИЯ [М2]")
        sv = res["связи"]
        r("Расход, кг/м²:", sv["расход_кгм2"])
        r("Масса, т:", sv["масса_т"])

        h("4. ПОДСТРОПИЛЬНЫЕ ФЕРМЫ")
        psf = res.get("подстроп", {})
        if "примечание" in psf:
            lines.append(f"  {psf['примечание']}")
        else:
            r("R, кН:", psf.get("R_кн",""))
            r("Расход М1, кг/м²:", psf.get("М1",""))
            r("Расход М2, кг/м²:", psf.get("М2",""))

        h("5. ПОДКРАНОВЫЕ БАЛКИ")
        pb = res["подкрановые"]
        r("Масса 1 балки (М1), т:", pb["G_1пб_т"])
        r("Балка (таблица), кг/м:", pb["балка_кгм"])
        r("Тормоза (таблица), кг/м:", pb["тормоз_кгм"])
        r("Расход М1, кг/м²:", pb["М1"])
        r("Расход М2, кг/м²:", pb["М2"])

        h("6. КОЛОННЫ [М1]")
        kl = res["колонны"]
        r("Кол-во колонн:", kl["n"])
        r("ΣFв, кН:", kl["ΣFv"])
        r("ΣFн, кН:", kl["ΣFn"])
        r("Масса 1 кол., кг:", kl["масса_1_кг"])
        r("Расход, кг/м²:", kl["расход_кгм2"])
        r("Масса, т:", kl["масса_т"])

        h("7. ФАХВЕРК [М2]")
        fh = res.get("фахверк", {})
        r("Расход, кг/м² стен:", fh.get("расход_кгм2_стен",""))
        r("Масса, т:", fh.get("масса_т",""))

        h("8. ОГРАЖДЕНИЕ (справочно)")
        og = res["ограждение"]
        r("Площадь стен, м²:", og["стены_м2"])
        r("Площадь кровли, м²:", og["кровля_м2"])

        h("9. ОПОРЫ ТРУБОПРОВОДОВ [М2]")
        op = res.get("опоры", {})
        r("Расход, кг/м²:", op.get("расход_кгм2",""))
        r("Масса, т:", op.get("масса_т",""))

        screen = self.sm.get_screen("result")
        screen.ids.result_text.text = "\n".join(lines)
        self.sm.current = "result"


if __name__ == "__main__":
    MetalApp().run()
