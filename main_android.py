#!/usr/bin/env python3
"""
Металлоёмкость производственных зданий — Android-версия на Kivy/KivyMD
Расчётное ядро идентично main.py (Метод 1 + Метод 2).
"""
import os
import sys
import math
import traceback

# ─────────────────────────────────────────────────────────
#  ПУТИ (одинаково работает как на Android, так и на ПК)
# ─────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
elif os.environ.get("ANDROID_ARGUMENT"):          # Buildozer runtime
    from android.storage import app_storage_path  # type: ignore
    BASE_DIR = app_storage_path()
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR         = os.path.join(BASE_DIR, "Тип 1 здания с кранами")
POKRYTIE_XLSX    = os.path.join(DATA_DIR, "металлоекмсоть покрытия.xlsx")
FAKHVERK_XLSX    = os.path.join(DATA_DIR, "Металлоёмкость фахверк.xlsx")
CRANE_BEAMS_DOCX = os.path.join(DATA_DIR, "Таблица металлоемкости на подкрановые конструкции.docx")
BRAKE_DOCX       = os.path.join(DATA_DIR, "Таблица металлоемкости на тормозные конструкции.docx")

# ─────────────────────────────────────────────────────────
#  РАСЧЁТНОЕ ЯДРО (скопировано из main.py без изменений)
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

def _read_pokrytie():
    import pandas as pd
    return pd.read_excel(POKRYTIE_XLSX, header=None, sheet_name=0)

def _read_fakhverk():
    import pandas as pd
    return pd.read_excel(FAKHVERK_XLSX, header=None, sheet_name="Расчеты")

def get_truss_mass(df, truss_type, span_m, load_tm):
    type_map = {"Уголки":"Фермы из уголков",
                "Двутавры":"Фермы из двутавров",
                "Молодечно":"Фермы молодечно"}
    sec = type_map.get(truss_type, "Фермы из уголков")
    span_lbl = f"Пролет {int(span_m)}м"
    sec_row = None
    for i, row in df.iterrows():
        if str(row[0]).strip() == sec: sec_row = i; break
    if sec_row is None: return None
    span_row = None
    for i in range(sec_row, min(sec_row+10, len(df))):
        if str(df.iloc[i,0]).strip() == span_lbl: span_row = i; break
    if span_row is None: return None
    loads, masses = [], []
    for col in range(1, len(df.iloc[span_row+1])):
        try:
            loads.append(float(df.iloc[span_row+1, col]))
            masses.append(float(df.iloc[span_row+2, col]))
        except: pass
    if not loads: return None
    return interp_table(loads, masses, load_tm)

def get_subtruss_mass(df, R_t):
    sub_row = None
    for i, row in df.iterrows():
        if str(row[0]).strip() == "Подстропильные фермы": sub_row = i; break
    if sub_row is None: return None
    loads, masses = [], []
    for col in range(1, len(df.iloc[sub_row+1])):
        try:
            loads.append(float(df.iloc[sub_row+1, col]))
            masses.append(float(df.iloc[sub_row+2, col]))
        except: pass
    if not loads: return None
    return interp_table(loads, masses, ceil_to_table(R_t, loads))

def get_bracing(q_t, bstep):
    if q_t <= 120: return 15.0 if bstep <= 6 else 35.0
    return 40.0 if bstep <= 6 else 55.0

def _parse_docx_rows(path, tidx):
    from docx import Document
    doc = Document(path)
    result = []
    for row in doc.tables[tidx].rows:
        seen, cells = set(), []
        for cell in row.cells:
            t = cell.text.strip().replace('\n',' ')
            if t not in seen: cells.append(t); seen.add(t)
        if any(c.strip() for c in cells): result.append(cells)
    return result

def get_crane_beam_kgm(q_t, span_m, n_cranes):
    try:
        if q_t <= 50:
            rows = _parse_docx_rows(CRANE_BEAMS_DOCX, 0)
            ss = f"{int(span_m)} м"
            for row in rows:
                if row and ss in row[0]:
                    vals=[float(c) for c in row[1:] if _is_num(c)]
                    if not vals: return None
                    q_ord=[5,10,20,32,50]
                    qi=min(range(len(q_ord)),key=lambda i:abs(q_ord[i]-q_t))
                    ci=qi*2+(0 if n_cranes==1 else 1)
                    return vals[ci] if ci<len(vals) else vals[0]
        else:
            rows = _parse_docx_rows(CRANE_BEAMS_DOCX, 1)
            ss = str(int(span_m))
            for row in rows:
                if row and row[0].startswith(ss):
                    vals=[float(c) for c in row[1:] if _is_num(c)]
                    if not vals: return None
                    q_ord=[80,100,125,200,400]
                    qi=min(range(len(q_ord)),key=lambda i:abs(q_ord[i]-q_t))
                    ci=qi*2+(0 if n_cranes==1 else 1)
                    return vals[ci] if ci<len(vals) else vals[0]
    except: pass
    return None

def get_brake_kgm(q_t, span_m, n_cranes, with_pass, is_edge):
    try:
        tidx = 0 if q_t<=50 else 1
        rows = _parse_docx_rows(BRAKE_DOCX, tidx)
        ss = f"{int(span_m)} м"
        rt = "Крайний" if is_edge else "Средний"
        pt = "С проходом" if with_pass else "Без прохода"
        for row in rows:
            rf = " ".join(row)
            if (row and ss in row[0]) and rt in rf and pt in rf:
                vals=[float(c) for c in row if _is_num(c)]
                if vals:
                    return vals[0 if n_cranes==1 else min(1,len(vals)-1)]
    except: pass
    return None

def get_fakhverk_kgm2(df, step_col, has_post, h_bld, rig_load):
    try:
        if step_col<=6 and has_post: tr=7
        elif step_col<=6: tr=5
        else: tr=6
        lc = 2 if rig_load<=0 else (5 if rig_load<=100 else 8)
        ho = 0 if h_bld<=10 else (1 if h_bld<=20 else 2)
        return float(df.iloc[tr, lc+ho])
    except: return None

def _is_num(s):
    try: float(s); return True
    except: return False

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

    missing=[f for f in[POKRYTIE_XLSX,FAKHVERK_XLSX,CRANE_BEAMS_DOCX,BRAKE_DOCX]
             if not os.path.exists(f)]
    if missing: raise FileNotFoundError("Файлы не найдены:\n"+"\n".join(
        os.path.basename(f) for f in missing))

    df_cov = _read_pokrytie()
    df_fakh= _read_fakhverk()
    res={}; log=[]

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
    mtr=get_truss_mass(df_cov,truss_type,L_span,Q_tm)
    g_m2=None; G_tr1_kg=None
    if mtr is not None:
        n_tr=L_build/B_step+1
        g_m2=round(mtr*1000*n_tr/S_floor,2)
        G_tr1_kg=mtr*1000
    res["фермы"]=dict(нагрузка_тм=round(Q_tm,3),М1=g_m1 or "н/п",М2=g_m2 or "н/п",
        масса_т_М2=round(g_m2*S_floor/1000,2) if g_m2 else "н/п")

    # 3. СВЯЗИ
    g_br=get_bracing(q_crane_t,B_step)
    res["связи"]=dict(расход_кгм2=g_br, масса_т=round(g_br*S_floor/1000,2))

    # 4. ПОДСТРОПИЛЬНЫЕ ФЕРМЫ
    if col_step==12 and B_step<col_step:
        R_kn=Q_tm*9.81*L_span/2; R_t=R_kn/9.81
        Rf=max(100,min(R_kn,400)); a=(Rf-100)*0.0002+0.044
        G_pf_t=a*144/9.81
        n_sub=(L_build/col_step)*(max(0,round(W_build/L_span)-1))
        if n_sub<=0: n_sub=L_build/col_step
        g_s1=round(G_pf_t*1000*n_sub/S_floor,2)
        ms=get_subtruss_mass(df_cov,R_t)
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
        G_m=(((pb_m or 0)+(br_m or 0))*L_pb*n_along*n_mid/1000)
        g_pb_m2=round((G_e+G_m)*1000/S_floor,2)
    res["подкрановые"]=dict(G_1пб_т=round(G_pb_t,2),
        М1=g_pb_m1, М2=g_pb_m2,
        балка_кгм=pb_e, тормоз_кгм=br_e)

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
    SFv=( Q_roof+Q_purlin+Q_snow+Q_dust)*col_step*L_span/2+Gw_up
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
    gf=get_fakhverk_kgm2(df_fakh,col_step,has_post,H_full,rig_load)
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
         +sf(res.get("подстроп",{}),"масса_т_М2",)*S_floor/1000
         +sf(res["подкрановые"],"масса_т_М2")*S_floor/1000
         +sf(res["колонны"],"масса_т")
         +sf(res["фахверк"],"масса_т")
         +sf(res["опоры"],"масса_т"))
    res["итого"]=dict(
        М1_т=round(tm1,2), М2_т=round(tm2,2),
        М1_кгм2=round(tm1*1000/S_floor,2),
        М2_кгм2=round(tm2*1000/S_floor,2))
    return res


# ─────────────────────────────────────────────────────────
#  KIVY UI
# ─────────────────────────────────────────────────────────
from kivy.config import Config
Config.set("graphics","minimum_width","360")
Config.set("graphics","minimum_height","640")

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.toolbar import MDTopAppBar
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.spinner import Spinner

KV = """
#:import dp kivy.metrics.dp

MDScreenManager:
    InputScreen:
    ResultScreen:

<InputScreen>:
    name: "input"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Металлоёмкость зданий"
            elevation: 4
            left_action_items: []
            md_bg_color: app.theme_cls.primary_color
        ScrollView:
            MDBoxLayout:
                id: form
                orientation: "vertical"
                padding: dp(16)
                spacing: dp(8)
                size_hint_y: None
                height: self.minimum_height

        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: dp(56)
            padding: dp(8), dp(4)
            spacing: dp(8)
            MDRaisedButton:
                text: "РАССЧИТАТЬ"
                on_release: app.do_calculate()
                size_hint_x: 1
                md_bg_color: app.theme_cls.primary_color
            MDFlatButton:
                text: "СБРОС"
                on_release: app.do_reset()

<ResultScreen>:
    name: "result"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Результаты"
            elevation: 4
            left_action_items: [["arrow-left", lambda x: app.go_back()]]
            md_bg_color: app.theme_cls.primary_color
        ScrollView:
            MDLabel:
                id: result_text
                text: ""
                font_name: "Roboto"
                size_hint_y: None
                height: self.texture_size[1]
                padding: dp(12), dp(8)
                markup: True
"""


class InputScreen(MDScreen):
    pass


class ResultScreen(MDScreen):
    pass


class MetalApp(MDApp):

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Dark"
        self.title = "Металлоёмкость зданий v1.0"
        root = Builder.load_string(KV)
        self.sm = root
        self._build_form(root.get_screen("input").ids.form)
        return root

    # ── Построение формы ─────────────────────────────────

    def _field(self, label, default, hint=""):
        box = MDBoxLayout(orientation="vertical", size_hint_y=None,
                          height=dp(72), spacing=0)
        tf = MDTextField(
            hint_text=label,
            helper_text=hint,
            helper_text_mode="on_focus",
            text=str(default),
            input_filter="float",
            size_hint_y=None, height=dp(64),
        )
        box.add_widget(tf)
        return box, tf

    def _section(self, title):
        lbl = MDLabel(text=f"[b]{title}[/b]", markup=True,
                      theme_text_color="Primary",
                      size_hint_y=None, height=dp(36))
        return lbl

    def _spinner_row(self, label, values, default):
        box = MDBoxLayout(orientation="vertical", size_hint_y=None, height=dp(80))
        box.add_widget(MDLabel(text=label, size_hint_y=None, height=dp(28),
                               font_style="Caption"))
        sp = Spinner(text=default, values=values,
                     size_hint=(1, None), height=dp(44),
                     background_color=(0.2, 0.45, 0.8, 1),
                     color=(1,1,1,1))
        box.add_widget(sp)
        return box, sp

    def _checkbox_row(self, label):
        box = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                          height=dp(48), spacing=dp(8))
        cb = MDCheckbox(size_hint=(None, None), size=(dp(40), dp(40)))
        box.add_widget(cb)
        box.add_widget(MDLabel(text=label))
        return box, cb

    def _build_form(self, form):
        F = form
        fields = {}
        def s(t): F.add_widget(self._section(t))
        def f(k, label, default, hint=""):
            box, tf = self._field(label, default, hint)
            F.add_widget(box)
            fields[k] = tf
        def sp(k, label, values, default):
            box, spinner = self._spinner_row(label, values, default)
            F.add_widget(box)
            fields[k] = spinner
        def cb(k, label):
            box, checkbox = self._checkbox_row(label)
            F.add_widget(box)
            fields[k] = checkbox

        s("Геометрия здания")
        f("L_build", "Длина здания по осям, м", 120)
        f("W_build", "Ширина здания, м", 48)
        f("L_span",  "Пролёт фермы L, м", 24)
        f("B_step",  "Шаг ферм B, м", 6)
        sp("col_step","Шаг колонн, м", ["6","12"], "12")
        f("h_rail",  "Уровень головки рельса, м", 8.0)

        s("Нагрузки (расчётные, кН/м²)")
        f("Q_snow",   "Снег (Qснег)", 2.1)
        f("Q_dust",   "Пыль (Qпыль)", 0.0)
        f("Q_roof",   "Кровля (Qкровля)", 0.65)
        f("Q_purlin", "Вес прогона (Qвес.прог.)", 0.35)
        f("yc",       "Коэф. уровня ответственности γc", 1.0)

        s("Стропильные фермы")
        sp("truss_type","Тип фермы",["Уголки","Двутавры","Молодечно"],"Уголки")

        s("Мостовой кран")
        f("q_crane_t","Грузоподъёмность крана, т", 50)
        sp("n_cranes","Кол-во кранов в пролёте",["1","2"],"1")
        sp("with_pass","Тормозные пути",["С проходом","Без прохода"],"С проходом")

        s("Фахверк")
        f("rig_load","Нагрузка на ригели фахверка, кг/м.п.", 0)
        cb("has_post","Наличие стойки фахверка (шаг 12 м)")

        s("Тип здания (опоры трубопроводов)")
        sp("bld_type","Тип здания",
           ["Основные производственные","Здания энергоносителей","Вспомогательные здания"],
           "Основные производственные")

        self._fields = fields

    # ── Считать параметры из формы ───────────────────────

    def _get(self, key, default=0.0):
        w = self._fields.get(key)
        if w is None: return default
        if hasattr(w, "text") and hasattr(w, "input_filter"):  # TextField
            try: return float(w.text.replace(",","."))
            except: return default
        if hasattr(w, "text"):  # Spinner
            return w.text
        if hasattr(w, "active"):  # Checkbox
            return w.active
        return default

    def _read_params(self):
        col_step = int(self._get("col_step", "12"))
        has_post = bool(self._get("has_post")) and col_step == 12
        return {
            "L_build":   self._get("L_build", 120),
            "W_build":   self._get("W_build", 48),
            "L_span":    self._get("L_span",  24),
            "B_step":    self._get("B_step",  6),
            "col_step":  col_step,
            "h_rail":    self._get("h_rail",  8),
            "Q_snow":    self._get("Q_snow",  2.1),
            "Q_dust":    self._get("Q_dust",  0),
            "Q_roof":    self._get("Q_roof",  0.65),
            "Q_purlin":  self._get("Q_purlin",0.35),
            "yc":        self._get("yc",      1.0),
            "truss_type":self._get("truss_type","Уголки"),
            "q_crane_t": self._get("q_crane_t",50),
            "n_cranes":  int(self._get("n_cranes","1")),
            "with_pass": self._get("with_pass","С проходом") == "С проходом",
            "rig_load":  self._get("rig_load",0),
            "has_post":  has_post,
            "bld_type":  self._get("bld_type","Основные производственные"),
        }

    # ── Навигация и действия ─────────────────────────────

    def go_back(self):
        self.sm.current = "input"

    def do_reset(self):
        self.sm.current = "input"

    def do_calculate(self):
        Snackbar(text="Выполняется расчёт…", duration=1).open()
        Clock.schedule_once(self._run_calc, 0.3)

    def _run_calc(self, dt):
        try:
            params = self._read_params()
            res = calculate(params)
            self._show_results(res)
        except FileNotFoundError as e:
            Snackbar(text=f"Файлы не найдены: {e}", duration=4).open()
        except Exception:
            tb = traceback.format_exc()
            screen = self.sm.get_screen("result")
            screen.ids.result_text.text = f"[color=ff4444]ОШИБКА:[/color]\n{tb}"
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
