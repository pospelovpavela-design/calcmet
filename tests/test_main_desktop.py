# -*- coding: utf-8 -*-
"""
Тесты для всех чистых расчётных функций main_desktop.py (v3.0).

Покрытие:
  • Вспомогательные функции (_lkp, ceil_to_table, interp_table)
  • Прогоны            (select_purlin, PURLIN_TABLE)
  • Кровельный пирог   (ROOF_MATERIALS)
  • Фермы              (get_truss_mass_m2, get_subtruss_mass_m2)
  • Связи              (get_bracing_kgm2)
  • Подкрановые балки  (get_crane_beam_kgm, get_brake_kgm, CRANE_MODE_FACTOR_M1/M2)
  • Фахверк            (get_fakhverk_kgm2)
  • Опоры труб         (get_pipe_support_kgm2)
  • Высоты колонн      (через calculate())
  • Полный расчёт      (calculate(), однопролётный и многопролётный)

Запуск: python -m pytest tests/test_main_desktop.py -v
"""

import sys
import os

# conftest.py уже зарегистрировал заглушки customtkinter/tkinter.
# Добавляем корень проекта в path на случай запуска файла напрямую.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from main_desktop import (
    _lkp,
    ceil_to_table,
    interp_table,
    select_purlin,
    get_truss_mass_m2,
    get_subtruss_mass_m2,
    get_bracing_kgm2,
    get_crane_beam_kgm,
    get_brake_kgm,
    get_fakhverk_kgm2,
    get_pipe_support_kgm2,
    calculate,
    PURLIN_TABLE,
    ROOF_MATERIALS,
    ROOF_PRESETS,
    CRANE_MODE_FACTOR_M1,
    CRANE_MODE_FACTOR_M2,
    CRANE_BEAM_ALPHA,
    RAIL_WEIGHT_KN,
    CRANE_Q_EQUIV,
    TRUSS_LOADS,
    TRUSS_MASSES,
    SUBTRUSS_LOADS,
    SUBTRUSS_MASSES,
    FAKHVERK_DATA,
)


# ─────────────────────────────────────────────────────────────────────────────
#  Вспомогательные функции
# ─────────────────────────────────────────────────────────────────────────────

class TestLkp:
    """_lkp — поиск с округлением вверх."""

    def test_exact_key(self):
        d = {10: "a", 20: "b", 30: "c"}
        assert _lkp(d, 20) == "b"

    def test_between_keys_returns_ceiling(self):
        d = {10: "a", 20: "b", 30: "c"}
        assert _lkp(d, 15) == "b"

    def test_below_min_returns_first(self):
        d = {10: "a", 20: "b"}
        assert _lkp(d, 1) == "a"

    def test_above_max_returns_last(self):
        d = {10: "a", 20: "b", 30: "c"}
        assert _lkp(d, 99) == "c"

    def test_float_keys(self):
        d = {5.0: 1.0, 10.0: 2.0}
        assert _lkp(d, 7.5) == pytest.approx(2.0)


class TestCeilToTable:
    """ceil_to_table — округление вверх до ближайшего табличного значения."""

    def test_exact_match(self):
        assert ceil_to_table(6, [6, 12, 18]) == 6

    def test_between(self):
        assert ceil_to_table(9, [6, 12, 18]) == 12

    def test_above_max_returns_last(self):
        assert ceil_to_table(100, [6, 12, 18, 24]) == 24

    def test_single_element(self):
        assert ceil_to_table(5, [12]) == 12


class TestInterpTable:
    """interp_table — поиск ближайшего верхнего значения по паре списков."""

    def test_exact_match(self):
        assert interp_table([1.0, 2.0, 3.0], [10, 20, 30], 2.0) == 20

    def test_between_takes_ceiling(self):
        assert interp_table([1.0, 2.0, 3.0], [10, 20, 30], 1.5) == 20

    def test_below_min_returns_first(self):
        assert interp_table([1.0, 2.0], [10, 20], 0.1) == 10

    def test_above_max_returns_last(self):
        assert interp_table([1.0, 2.0], [10, 20], 99.0) == 20


# ─────────────────────────────────────────────────────────────────────────────
#  Прогоны
# ─────────────────────────────────────────────────────────────────────────────

class TestPurlinTable:
    """Структурные проверки PURLIN_TABLE."""

    def test_has_six_rows(self):
        assert len(PURLIN_TABLE) == 6

    def test_tuple_length_five(self):
        for row in PURLIN_TABLE:
            assert len(row) == 5, f"Строка {row} должна иметь 5 полей"

    def test_qp_max_ascending(self):
        qps = [row[0] for row in PURLIN_TABLE]
        assert qps == sorted(qps), "qp_max должны возрастать"

    def test_mass_6m_positive(self):
        for row in PURLIN_TABLE:
            assert row[2] > 0, f"Масса B=6м должна быть положительной: {row}"

    def test_mass_12m_positive(self):
        for row in PURLIN_TABLE:
            assert row[4] > 0, f"Масса B=12м должна быть положительной: {row}"

    def test_mass_12m_greater_than_6m(self):
        """Двутавр 12 м тяжелее швеллера 6 м."""
        for row in PURLIN_TABLE:
            assert row[4] > row[2], (
                f"Масса B=12м ({row[4]}) должна быть > B=6м ({row[2]}): {row}"
            )

    def test_name_6m_is_channel(self):
        for row in PURLIN_TABLE:
            assert "Швеллер" in row[1], f"B=6м должен быть швеллер: {row[1]}"

    def test_name_12m_is_ibeam(self):
        for row in PURLIN_TABLE:
            assert "Двутавр" in row[3], f"B=12м должен быть двутавр: {row[3]}"


class TestSelectPurlin:
    """select_purlin — подбор профиля по нагрузке и шагу ферм."""

    def test_light_load_b6_returns_channel(self):
        mass, name = select_purlin(0.20, 6)
        assert "Швеллер" in name
        assert mass == pytest.approx(110.4)

    def test_light_load_b12_returns_ibeam(self):
        mass, name = select_purlin(0.20, 12)
        assert "Двутавр" in name
        assert mass > 300

    def test_heavy_load_b6_heavier_profile(self):
        mass_light, _ = select_purlin(0.20, 6)
        mass_heavy, _ = select_purlin(1.50, 6)
        assert mass_heavy > mass_light

    def test_heavy_load_b12_heavier_profile(self):
        mass_light, _ = select_purlin(0.20, 12)
        mass_heavy, _ = select_purlin(1.50, 12)
        assert mass_heavy > mass_light

    def test_b6_vs_b12_same_load(self):
        """При одинаковой нагрузке B=12м даёт более тяжёлый прогон."""
        mass6, _ = select_purlin(0.50, 6)
        mass12, _ = select_purlin(0.50, 12)
        assert mass12 > mass6

    def test_exact_boundary_inclusive(self):
        """Нагрузка ровно на границе строки → эта строка."""
        mass, name = select_purlin(0.45, 6)
        assert mass == pytest.approx(110.4)
        assert name == "Швеллер 20"

    def test_overload_returns_last_with_exclamation(self):
        _, name = select_purlin(99.0, 6)
        assert "!" in name

    def test_b_step_5_treated_as_6(self):
        """Шаг ≤ 6 м → колонка B=6."""
        m5, n5 = select_purlin(0.20, 5)
        m6, n6 = select_purlin(0.20, 6)
        assert m5 == m6 and n5 == n6


# ─────────────────────────────────────────────────────────────────────────────
#  Кровельный пирог
# ─────────────────────────────────────────────────────────────────────────────

class TestRoofMaterials:
    """Проверка данных ROOF_MATERIALS и ROOF_PRESETS."""

    def test_all_weights_positive(self):
        for name, w in ROOF_MATERIALS.items():
            assert w > 0, f"Вес материала '{name}' должен быть > 0"

    def test_all_weights_reasonable(self):
        """Веса в диапазоне 0.001–1.0 кН/м² (физически обоснованно)."""
        for name, w in ROOF_MATERIALS.items():
            assert 0.001 <= w <= 1.0, f"Вес '{name}' = {w} выходит за диапазон"

    def test_profnastil_lighter_than_strazka(self):
        prof = ROOF_MATERIALS["Профнастил Н-75 (t=0.8мм)"]
        strazka = ROOF_MATERIALS["Стяжка цементная 30мм"]
        assert strazka > prof

    def test_thicker_minvata_heavier(self):
        m100 = ROOF_MATERIALS["Минвата 100мм (ρ=80 кг/м³)"]
        m200 = ROOF_MATERIALS["Минвата 200мм (ρ=80 кг/м³)"]
        assert m200 > m100

    def test_thicker_pir_heavier(self):
        p100 = ROOF_MATERIALS["PIR-плита 100мм (ρ=35 кг/м³)"]
        p200 = ROOF_MATERIALS["PIR-плита 200мм (ρ=35 кг/м³)"]
        assert p200 > p100

    def test_pir_lighter_than_minvata_same_thickness(self):
        """PIR легче минваты при одинаковой толщине (ρ=35 vs 80 кг/м³)."""
        pir = ROOF_MATERIALS["PIR-плита 150мм (ρ=35 кг/м³)"]
        mw = ROOF_MATERIALS["Минвата 150мм (ρ=80 кг/м³)"]
        assert pir < mw

    def test_sandwich_panel_heavier_than_profnastil(self):
        sp = ROOF_MATERIALS["Сэндвич-панель кровельная 200мм"]
        pn = ROOF_MATERIALS["Профнастил Н-75 (t=0.8мм)"]
        assert sp > pn

    def test_presets_keys_in_materials(self):
        """Каждый материал из пресетов есть в ROOF_MATERIALS."""
        for preset_name, layers in ROOF_PRESETS.items():
            for mat in layers:
                assert mat in ROOF_MATERIALS, (
                    f"Пресет '{preset_name}': материал '{mat}' не найден в ROOF_MATERIALS"
                )

    def test_preset_total_positive(self):
        for preset_name, layers in ROOF_PRESETS.items():
            total = sum(ROOF_MATERIALS[m] for m in layers)
            assert total > 0, f"Пресет '{preset_name}' даёт нулевой вес"


# ─────────────────────────────────────────────────────────────────────────────
#  Фермы
# ─────────────────────────────────────────────────────────────────────────────

class TestTruss:
    """get_truss_mass_m2 — масса стропильной фермы из таблицы М2."""

    def test_all_truss_types_return_value_for_l24(self):
        for tt in ("Уголки", "Двутавры", "Молодечно"):
            m = get_truss_mass_m2(tt, 24, 4.0)
            assert m is not None and m > 0, f"Тип {tt}: нет данных для L=24"

    def test_heavier_load_heavier_truss(self):
        for tt in ("Уголки", "Двутавры", "Молодечно"):
            m_light = get_truss_mass_m2(tt, 24, 2.0)
            m_heavy = get_truss_mass_m2(tt, 24, 10.0)
            assert m_heavy >= m_light, f"{tt}: тяжелее нагрузка → должна быть тяжелее ферма"

    def test_longer_span_heavier_truss(self):
        for tt in ("Уголки", "Двутавры", "Молодечно"):
            m18 = get_truss_mass_m2(tt, 18, 4.0)
            m36 = get_truss_mass_m2(tt, 36, 4.0)
            assert m36 > m18, f"{tt}: L=36м должна быть тяжелее L=18м"

    def test_unknown_type_returns_none(self):
        assert get_truss_mass_m2("НеизвестныйТип", 24, 4.0) is None

    def test_truss_loads_and_masses_same_length(self):
        """Все строки TRUSS_MASSES совпадают по длине с TRUSS_LOADS."""
        for tt, by_span in TRUSS_MASSES.items():
            for span, masses in by_span.items():
                assert len(masses) == len(TRUSS_LOADS), (
                    f"{tt}[{span}]: {len(masses)} масс, ожидалось {len(TRUSS_LOADS)}"
                )

    def test_all_masses_positive(self):
        for tt, by_span in TRUSS_MASSES.items():
            for span, masses in by_span.items():
                for m in masses:
                    assert m > 0, f"TRUSS_MASSES[{tt}][{span}] содержит 0 или < 0"


class TestSubtruss:
    """get_subtruss_mass_m2 — подстропильные фермы."""

    def test_returns_positive_for_valid_load(self):
        for r in [18.0, 72.0, 180.0]:
            m = get_subtruss_mass_m2(r)
            assert m is not None and m > 0, f"R={r}: ожидалось положительное значение"

    def test_heavier_load_heavier_subtruss(self):
        m1 = get_subtruss_mass_m2(18.0)
        m2 = get_subtruss_mass_m2(216.0)
        assert m2 >= m1

    def test_subtruss_data_same_length(self):
        assert len(SUBTRUSS_LOADS) == len(SUBTRUSS_MASSES)

    def test_subtruss_loads_ascending(self):
        assert SUBTRUSS_LOADS == sorted(SUBTRUSS_LOADS)


# ─────────────────────────────────────────────────────────────────────────────
#  Связи по покрытию
# ─────────────────────────────────────────────────────────────────────────────

class TestBracing:
    """get_bracing_kgm2 — связи зависят от г/п и шага ферм."""

    def test_light_crane_b6(self):
        assert get_bracing_kgm2(50, 6) == pytest.approx(15.0)

    def test_light_crane_b12(self):
        assert get_bracing_kgm2(50, 12) == pytest.approx(35.0)

    def test_heavy_crane_b6(self):
        assert get_bracing_kgm2(200, 6) == pytest.approx(40.0)

    def test_heavy_crane_b12(self):
        assert get_bracing_kgm2(200, 12) == pytest.approx(55.0)

    def test_boundary_120t(self):
        """г/п = 120т — переходная точка к тяжёлым связям."""
        assert get_bracing_kgm2(120, 6) == pytest.approx(15.0)
        assert get_bracing_kgm2(121, 6) == pytest.approx(40.0)

    def test_wider_step_heavier_bracing(self):
        for q in [50, 100, 200]:
            assert get_bracing_kgm2(q, 12) > get_bracing_kgm2(q, 6)


# ─────────────────────────────────────────────────────────────────────────────
#  Подкрановые балки
# ─────────────────────────────────────────────────────────────────────────────

class TestCraneBeamAlpha:
    """CRANE_BEAM_ALPHA — коэффициент αпб растёт с г/п."""

    def test_monotone_increasing(self):
        qs = sorted(CRANE_BEAM_ALPHA)
        vals = [CRANE_BEAM_ALPHA[q] for q in qs]
        for i in range(len(vals) - 1):
            assert vals[i] <= vals[i + 1]

    def test_all_positive(self):
        for q, a in CRANE_BEAM_ALPHA.items():
            assert a > 0, f"αпб[{q}] = {a}"


class TestRailWeight:
    """RAIL_WEIGHT_KN — масса рельса растёт с г/п."""

    def test_monotone_non_decreasing(self):
        qs = sorted(RAIL_WEIGHT_KN)
        vals = [RAIL_WEIGHT_KN[q] for q in qs]
        for i in range(len(vals) - 1):
            assert vals[i] <= vals[i + 1]


class TestCraneModeFactor:
    """Коэффициенты режима работы крана."""

    def test_m1_16k_is_one(self):
        assert CRANE_MODE_FACTOR_M1["Режим 1-6К"] == pytest.approx(1.00)

    def test_m1_78k_is_1_80(self):
        """7-8К скорректирован: 1.15 → 1.80 (калибровка по методике)."""
        assert CRANE_MODE_FACTOR_M1["Режим 7-8К"] == pytest.approx(1.80)

    def test_m2_78k_is_1_80(self):
        """7-8К скорректирован: 1.15 → 1.80 (калибровка по методике)."""
        assert CRANE_MODE_FACTOR_M2["Режим 7-8К"] == pytest.approx(1.80)

    def test_m2_16k_less_than_78k(self):
        assert CRANE_MODE_FACTOR_M2["Режим 1-6К"] < CRANE_MODE_FACTOR_M2["Режим 7-8К"]

    def test_m2_16k_reduction_60_to_70_percent(self):
        """1-6К даёт 60–70% снижения относительно 7-8К (0.65/1.80 = 63.9%)."""
        ratio = CRANE_MODE_FACTOR_M2["Режим 1-6К"] / CRANE_MODE_FACTOR_M2["Режим 7-8К"]
        reduction_pct = (1 - ratio) * 100
        assert 60 <= reduction_pct <= 70, (
            f"Снижение М2: {reduction_pct:.1f}% — ожидалось 60–70%"
        )

    def test_m2_78k_same_as_m1_78k(self):
        """Для 7-8К оба метода дают одинаковый коэффициент."""
        assert (
            CRANE_MODE_FACTOR_M2["Режим 7-8К"]
            == pytest.approx(CRANE_MODE_FACTOR_M1["Режим 7-8К"])
        )

    def test_both_dicts_have_same_keys(self):
        assert set(CRANE_MODE_FACTOR_M1) == set(CRANE_MODE_FACTOR_M2)


class TestGetCraneBeam:
    """get_crane_beam_kgm — масса подкрановой балки из таблицы."""

    def test_returns_positive_t1(self):
        result = get_crane_beam_kgm(20, 6, 1)
        assert result is not None and result > 0

    def test_returns_positive_t2(self):
        result = get_crane_beam_kgm(100, 12, 1)
        assert result is not None and result > 0

    def test_two_cranes_heavier(self):
        m1 = get_crane_beam_kgm(20, 6, 1)
        m2 = get_crane_beam_kgm(20, 6, 2)
        assert m2 >= m1

    def test_larger_span_heavier(self):
        m6 = get_crane_beam_kgm(20, 6, 1)
        m12 = get_crane_beam_kgm(20, 12, 1)
        assert m12 >= m6

    def test_heavier_crane_heavier_beam(self):
        m20 = get_crane_beam_kgm(20, 6, 1)
        m50 = get_crane_beam_kgm(50, 6, 1)
        assert m50 >= m20


class TestGetBrake:
    """get_brake_kgm — масса тормозных конструкций."""

    def test_returns_positive_edge_with_passage(self):
        result = get_brake_kgm(20, 6, 1, True, True)
        assert result is not None and result > 0

    def test_returns_positive_middle_no_passage(self):
        result = get_brake_kgm(20, 6, 1, False, False)
        assert result is not None and result > 0

    def test_with_passage_heavier_or_equal(self):
        """С проходом ≥ без прохода для крайних рядов."""
        with_p = get_brake_kgm(20, 6, 1, True, True)
        no_p = get_brake_kgm(20, 6, 1, False, True)
        assert with_p >= no_p

    def test_t2_heavy_crane(self):
        result = get_brake_kgm(100, 12, 1, True, True)
        assert result is not None and result > 0


# ─────────────────────────────────────────────────────────────────────────────
#  Фахверк
# ─────────────────────────────────────────────────────────────────────────────

class TestFakhverk:
    """get_fakhverk_kgm2 — масса фахверка по типу и параметрам."""

    def test_type_i_returns_value(self):
        v = get_fakhverk_kgm2(6, False, 8, 0)
        assert v is not None and v > 0

    def test_type_ii_returns_value(self):
        v = get_fakhverk_kgm2(12, False, 8, 0)
        assert v is not None and v > 0

    def test_type_iii_with_post_returns_value(self):
        v = get_fakhverk_kgm2(6, True, 8, 0)
        assert v is not None and v > 0

    def test_type_iii_heavier_than_type_i(self):
        """Фахверк III (с промежуточной стойкой) тяжелее типа I."""
        v_i = get_fakhverk_kgm2(6, False, 8, 0)
        v_iii = get_fakhverk_kgm2(6, True, 8, 0)
        assert v_iii >= v_i

    def test_taller_building_heavier_fakhverk(self):
        v_low = get_fakhverk_kgm2(6, False, 8, 0)
        v_high = get_fakhverk_kgm2(6, False, 22, 0)
        assert v_high >= v_low

    def test_high_rig_load_heavier(self):
        v0 = get_fakhverk_kgm2(6, False, 8, 0)
        v200 = get_fakhverk_kgm2(6, False, 8, 200)
        assert v200 >= v0

    def test_all_fakhverk_data_positive(self):
        for key, val in FAKHVERK_DATA.items():
            assert val > 0, f"FAKHVERK_DATA[{key}] = {val}"


# ─────────────────────────────────────────────────────────────────────────────
#  Опоры трубопроводов
# ─────────────────────────────────────────────────────────────────────────────

class TestPipeSupport:
    """get_pipe_support_kgm2 — расход на опоры трубопроводов."""

    def test_main_production(self):
        v = get_pipe_support_kgm2("Основные производственные")
        assert 11 <= v <= 22

    def test_energy(self):
        v = get_pipe_support_kgm2("Здания энергоносителей")
        assert 23 <= v <= 40

    def test_auxiliary(self):
        v = get_pipe_support_kgm2("Вспомогательные здания")
        assert 2 <= v <= 4

    def test_energy_heavier_than_main(self):
        assert get_pipe_support_kgm2("Здания энергоносителей") > \
               get_pipe_support_kgm2("Основные производственные")

    def test_unknown_type_returns_default(self):
        """Неизвестный тип → значение по умолчанию, не исключение."""
        v = get_pipe_support_kgm2("Несуществующий тип")
        assert v > 0


# ─────────────────────────────────────────────────────────────────────────────
#  Полный расчёт calculate()
# ─────────────────────────────────────────────────────────────────────────────

def _gp(**kw):
    """Глобальные параметры с разумными значениями по умолчанию."""
    base = dict(L_build=120.0, Q_snow=2.1, Q_dust=0.0, Q_tech=0.0, yc=1.0)
    base.update(kw)
    return base


def _sp(**kw):
    """Параметры одного пролёта с разумными значениями по умолчанию."""
    base = dict(
        L_span=24.0,
        B_step=6.0,
        col_step=6.0,
        h_rail=10.0,
        H_col_ov=0.0,
        Q_roof=0.20,
        Q_purlin=0.35,
        truss_type="Уголки",
        q_crane_t=20.0,
        n_cranes=1,
        with_pass=True,
        crane_mode="Режим 1-6К",
        rig_load=0.0,
        has_post=False,
        bld_type="Основные производственные",
    )
    base.update(kw)
    return base


class TestCalculateSingleSpan:
    """Однопролётный полный расчёт."""

    def test_runs_without_exception(self):
        res = calculate(_gp(), [_sp()])
        assert isinstance(res, dict)

    def test_result_has_all_main_sections(self):
        res = calculate(_gp(), [_sp()])
        expected_keys = {
            "прогоны", "фермы", "связи_покрытия",
            "подстропильные_фермы", "подкрановые_балки",
            "колонны", "фахверк", "опоры_трубопроводов", "итого",
        }
        assert expected_keys.issubset(res.keys())

    def test_total_mass_positive(self):
        res = calculate(_gp(), [_sp()])
        assert res["итого"]["М1_т"] > 0

    def test_total_m2_positive_for_ibeam(self):
        res = calculate(_gp(), [_sp(truss_type="Двутавры")])
        assert res["итого"]["М2_т"] > 0

    def test_purlin_mass_positive(self):
        res = calculate(_gp(), [_sp()])
        assert res["прогоны"]["масса_общая_т"] > 0

    def test_columns_mass_positive(self):
        res = calculate(_gp(), [_sp()])
        assert res["колонны"]["масса_общая_т"] > 0

    def test_crane_beam_m1_positive(self):
        res = calculate(_gp(), [_sp()])
        assert res["подкрановые_балки"]["масса_общая_т_М1"] > 0

    def test_floor_area_correct(self):
        res = calculate(_gp(L_build=120.0), [_sp(L_span=24.0)])
        assert res["итого"]["S_floor"] == pytest.approx(120.0 * 24.0, rel=0.01)

    def test_heavier_snow_increases_total(self):
        res_low = calculate(_gp(Q_snow=1.0), [_sp()])
        res_high = calculate(_gp(Q_snow=3.5), [_sp()])
        assert res_high["итого"]["М1_т"] > res_low["итого"]["М1_т"]

    def test_heavier_yc_increases_total(self):
        res1 = calculate(_gp(yc=1.0), [_sp()])
        res2 = calculate(_gp(yc=1.2), [_sp()])
        assert res2["итого"]["М1_т"] > res1["итого"]["М1_т"]

    def test_longer_building_heavier(self):
        res60 = calculate(_gp(L_build=60.0), [_sp()])
        res120 = calculate(_gp(L_build=120.0), [_sp()])
        assert res120["итого"]["М1_т"] > res60["итого"]["М1_т"]

    def test_doubling_length_roughly_doubles_mass(self):
        r60 = calculate(_gp(L_build=60.0), [_sp()])
        r120 = calculate(_gp(L_build=120.0), [_sp()])
        ratio = r120["итого"]["М1_т"] / r60["итого"]["М1_т"]
        assert 1.5 <= ratio <= 2.5

    def test_wider_span_increases_total(self):
        res24 = calculate(_gp(), [_sp(L_span=24.0)])
        res36 = calculate(_gp(), [_sp(L_span=36.0)])
        assert res36["итого"]["М1_т"] > res24["итого"]["М1_т"]

    def test_col_step_12_has_subtruss(self):
        """Шаг колонн 12 м → есть подстропильные фермы."""
        res = calculate(_gp(), [_sp(col_step=12.0)])
        st = res["подстропильные_фермы"]
        m1 = st.get("масса_общая_т_М1", 0) or 0
        m2 = st.get("масса_общая_т_М2", 0) or 0
        assert (m1 + m2) > 0, "Подстропильные фермы при col_step=12 должны быть ненулевыми"

    def test_col_step_6_no_subtruss(self):
        """Шаг колонн 6 м → подстропильные фермы не нужны."""
        res = calculate(_gp(), [_sp(col_step=6.0)])
        st = res["подстропильные_фермы"]
        m1 = st.get("масса_общая_т_М1", 0) or 0
        m2 = st.get("масса_общая_т_М2", 0) or 0
        assert (m1 + m2) == 0


class TestCalculateCraneMode:
    """Режим крана влияет на подкрановые балки."""

    def test_m1_78k_heavier_than_16k(self):
        res16 = calculate(_gp(), [_sp(crane_mode="Режим 1-6К")])
        res78 = calculate(_gp(), [_sp(crane_mode="Режим 7-8К")])
        pb16 = res16["подкрановые_балки"]["масса_общая_т_М1"]
        pb78 = res78["подкрановые_балки"]["масса_общая_т_М1"]
        assert pb78 > pb16, "М1: 7-8К должен быть тяжелее 1-6К"

    def test_m1_78k_is_80pct_more(self):
        """М1: ровно ×1.80 при переходе с 1-6К на 7-8К (коэф. скорректирован)."""
        res16 = calculate(_gp(), [_sp(crane_mode="Режим 1-6К")])
        res78 = calculate(_gp(), [_sp(crane_mode="Режим 7-8К")])
        pb16 = res16["подкрановые_балки"]["масса_общая_т_М1"]
        pb78 = res78["подкрановые_балки"]["масса_общая_т_М1"]
        assert pb78 / pb16 == pytest.approx(1.80, rel=0.01)

    def test_m2_78k_heavier_than_16k(self):
        res16 = calculate(_gp(), [_sp(truss_type="Двутавры", crane_mode="Режим 1-6К")])
        res78 = calculate(_gp(), [_sp(truss_type="Двутавры", crane_mode="Режим 7-8К")])
        pb16 = res16["подкрановые_балки"].get("масса_общая_т_М2", 0)
        pb78 = res78["подкрановые_балки"].get("масса_общая_т_М2", 0)
        if isinstance(pb16, str) or isinstance(pb78, str):
            pytest.skip("М2 недоступен для данных параметров")
        assert pb78 > pb16, "М2: 7-8К должен быть тяжелее 1-6К"

    def test_m2_16k_reduction_60_to_70_pct(self):
        """М2: снижение 1-6К относительно 7-8К в диапазоне 60–70% (0.65/1.80=63.9%)."""
        res16 = calculate(_gp(), [_sp(truss_type="Двутавры", crane_mode="Режим 1-6К")])
        res78 = calculate(_gp(), [_sp(truss_type="Двутавры", crane_mode="Режим 7-8К")])
        pb16 = res16["подкрановые_балки"].get("масса_общая_т_М2", 0)
        pb78 = res78["подкрановые_балки"].get("масса_общая_т_М2", 0)
        if isinstance(pb16, str) or isinstance(pb78, str):
            pytest.skip("М2 недоступен для данных параметров")
        if pb78 == 0:
            pytest.skip("М2 7-8К = 0")
        reduction = (1 - pb16 / pb78) * 100
        assert 60 <= reduction <= 70, (
            f"М2: снижение {reduction:.1f}% — ожидалось 60–70%"
        )


class TestCalculatePurlin:
    """Прогоны в полном расчёте."""

    def test_b12_purlin_heavier_than_b6(self):
        """Шаг ферм 12 м → прогоны тяжелее из-за двутавров."""
        res6 = calculate(_gp(), [_sp(B_step=6.0)])
        res12 = calculate(_gp(), [_sp(B_step=12.0)])
        m6 = res6["прогоны"]["масса_общая_т"]
        m12 = res12["прогоны"]["масса_общая_т"]
        assert m12 > m6

    def test_purlin_profile_in_result(self):
        res = calculate(_gp(), [_sp(B_step=6.0)])
        row = res["прогоны"]["по_пролётам"][0]
        assert "профиль" in row
        assert "Швеллер" in row["профиль"]

    def test_purlin_profile_b12_is_ibeam(self):
        res = calculate(_gp(), [_sp(B_step=12.0)])
        row = res["прогоны"]["по_пролётам"][0]
        assert "Двутавр" in row["профиль"]


class TestCalculateMultiSpan:
    """Многопролётные расчёты."""

    def test_two_spans_no_error(self):
        spans = [_sp(L_span=24.0), _sp(L_span=30.0)]
        res = calculate(_gp(), spans)
        assert res["итого"]["М1_т"] > 0

    def test_three_spans_no_error(self):
        spans = [_sp(L_span=18.0), _sp(L_span=24.0), _sp(L_span=30.0)]
        res = calculate(_gp(), spans)
        assert res["итого"]["М1_т"] > 0

    def test_area_sums_all_spans(self):
        spans = [_sp(L_span=24.0), _sp(L_span=30.0)]
        res = calculate(_gp(L_build=60.0), spans)
        expected = 60.0 * (24.0 + 30.0)
        assert res["итого"]["S_floor"] == pytest.approx(expected, rel=0.01)

    def test_two_spans_heavier_than_one(self):
        res1 = calculate(_gp(), [_sp(L_span=24.0)])
        res2 = calculate(_gp(), [_sp(L_span=24.0), _sp(L_span=24.0)])
        assert res2["итого"]["М1_т"] > res1["итого"]["М1_т"]

    def test_mixed_col_steps(self):
        """Разные шаги колонн в пролётах не вызывают ошибок."""
        spans = [_sp(col_step=6.0), _sp(col_step=12.0)]
        res = calculate(_gp(), spans)
        assert res["итого"]["М1_т"] > 0

    def test_mixed_crane_capacities(self):
        spans = [_sp(q_crane_t=20.0), _sp(q_crane_t=80.0)]
        res = calculate(_gp(), spans)
        assert res["итого"]["М1_т"] > 0

    def test_two_spans_purlin_count_equals_spans(self):
        spans = [_sp(L_span=24.0), _sp(L_span=30.0)]
        res = calculate(_gp(), spans)
        assert len(res["прогоны"]["по_пролётам"]) == 2

    def test_log_present(self):
        res = calculate(_gp(), [_sp()])
        assert "_log" in res


class TestCalculateColumnHeights:
    """Высоты колонн через полный расчёт."""

    def test_higher_rail_level_heavier_columns(self):
        res_low = calculate(_gp(), [_sp(h_rail=8.0)])
        res_high = calculate(_gp(), [_sp(h_rail=14.0)])
        assert res_high["колонны"]["масса_общая_т"] > res_low["колонны"]["масса_общая_т"]

    def test_override_h_col_changes_result(self):
        res_auto = calculate(_gp(), [_sp(H_col_ov=0.0)])
        res_override = calculate(_gp(), [_sp(H_col_ov=20.0)])
        assert res_override["колонны"]["масса_общая_т"] != \
               res_auto["колонны"]["масса_общая_т"]

    def test_h_r_tables_crane_20t(self):
        """h_r = 0.130 для крана 20 т (КР70)."""
        # Косвенно: разные h_r → разные высоты → разные колонны
        res20 = calculate(_gp(), [_sp(q_crane_t=20.0)])
        res50 = calculate(_gp(), [_sp(q_crane_t=50.0)])
        # Просто проверяем, что оба расчёта дают ненулевые результаты
        assert res20["колонны"]["масса_общая_т"] > 0
        assert res50["колонны"]["масса_общая_т"] > 0


# ─────────────────────────────────────────────────────────────────────────────
#  Эталонные тесты по методике
# ─────────────────────────────────────────────────────────────────────────────

class TestEtalonBlok1Purlins:
    """Блок 1. Прогоны — эталон по PURLIN_TABLE (методика, разд. 3).

    Входные данные:
      Q_snow=1.2 кН/м² (II снеговой р-н), Q_roof=0.30, Q_purlin=0.25,
      B_step=6 м, γn=1.0, a_пр=3.0 м (шаг прогонов).

    Ручной расчёт:
      qp = (0.30 + 0.25 + 1.20) × 3.0 × 1.0 / 9.81 = 0.535 т/м
      PURLIN_TABLE: 0.535 > 0.45 → следующий порог 0.65 → Швеллер 22, 126.0 кг
    """

    def test_qp_exceeds_first_threshold(self):
        """qp=0.535 т/м выходит за первый порог (0.45) — нужен Швеллер 22."""
        mass, name = select_purlin(0.535, 6)
        assert "22" in name, f"Ожидался Швеллер 22, получен {name}"

    def test_purlin_mass_b6(self):
        """Масса Швеллера 22 на 6 м = 126.0 кг."""
        mass, name = select_purlin(0.535, 6)
        assert mass == pytest.approx(126.0, rel=0.01)

    def test_boundary_exact_45_returns_channel20(self):
        """Граничное значение qp=0.45 → Швеллер 20, 110.4 кг."""
        mass, name = select_purlin(0.45, 6)
        assert "20" in name
        assert mass == pytest.approx(110.4, rel=0.01)

    def test_light_load_b12_returns_beam(self):
        """При шаге B=12 м подбирается двутавр, а не швеллер."""
        mass, name = select_purlin(0.30, 12)
        assert "Двутавр" in name or "Б" in name


class TestEtalonBlok2Trusses:
    """Блок 2. Стропильные фермы — эталон из таблицы TRUSS_MASSES (методика, разд. 2).

    Контрольный пример:
      Тип = Уголки, L = 24 м, Q_tm = 4.0 т/м
      → TRUSS_LOADS[4] = 4.0 → TRUSS_MASSES["Уголки"][24][4] = 4.29 кг/м²
    """

    def test_ugolki_24m_4tm_exact(self):
        """Уголки, L=24м, Q_tm=4.0 т/м → 4.29 кг/м² (из таблицы методики)."""
        mt = get_truss_mass_m2("Уголки", 24, 4.0)
        assert mt == pytest.approx(4.29, rel=0.001)

    def test_ugolki_24m_2tm_exact(self):
        """Уголки, L=24м, Q_tm=2.0 т/м → 2.30 кг/м² (первое значение таблицы)."""
        mt = get_truss_mass_m2("Уголки", 24, 2.0)
        assert mt == pytest.approx(2.30, rel=0.001)

    def test_ugolki_18m_lighter_than_36m(self):
        """Пролёт 18м легче, чем 36м при одинаковой нагрузке."""
        mt18 = get_truss_mass_m2("Уголки", 18, 4.0)
        mt36 = get_truss_mass_m2("Уголки", 36, 4.0)
        assert mt18 < mt36

    def test_all_truss_types_return_positive(self):
        """Все типы ферм дают положительный результат для типовых входных данных."""
        for tt in ["Уголки", "Двутавры", "Молодечно"]:
            mt = get_truss_mass_m2(tt, 24, 4.0)
            assert mt is not None and mt > 0, f"{tt}: ожидался mt > 0"


class TestEtalonBlok3CraneBeamM1:
    """Блок 3. Подкрановые балки М1 — эталон по методике ЦНИИ, разд. 5.1.

    Контрольный пример: Q_кран=100 т, L_пб=6 м, Режим 7-8К, 1 кран.
    Формула: Gпб = (αпб×Lпб + qр) × Lпб × kпб / 9.81 × mf_m1
      αпб=0.39 (методика, пример Q=100/20 т), qр=1.135 кН/м, kпб=1.2
      = (0.39×6 + 1.135) × 6 × 1.2 / 9.81 × 1.80
      = 3.475 × 7.2 / 9.81 × 1.80
      = 4.591 т/пролёт

    Эталон из методики (стр. "Подкрановые балки"):
      Gпб,n = (0.39×6 + 1.13)×6×1.2 = 24.98 кН ≈ 2498 кг (режим 1-6К).
      Режим 7-8К: ×1.80 → 4498 кг = 4.498 т ≈ 4.591 т (расхождение ~2% из-за g=9.81 vs 10).
    """

    def test_m1_100t_6m_78k_per_bay(self):
        """100т, 6м, 7-8К: масса одного ряда = 45.91 т (10 пролётов по 60 м)."""
        res = calculate(
            {"L_build": 60, "Q_snow": 2.1, "Q_dust": 0, "Q_tech": 0, "yc": 1.0},
            [_sp(q_crane_t=100, col_step=6, crane_mode="Режим 7-8К")],
        )
        # L_build=60 / col_step=6 = 10 пролётов; G1t≈4.591 т × 10 = 45.91 т
        row = res["подкрановые_балки"]["ряды_колонн"][0]
        assert row["G_М1_т"] == pytest.approx(45.91, rel=0.02)

    def test_m1_78k_heavier_than_16k_100t(self):
        """Режим 7-8К даёт тяжелее балки, чем 1-6К (в ×1.80 раз)."""
        res16 = calculate(
            {"L_build": 60, "Q_snow": 2.1, "Q_dust": 0, "Q_tech": 0, "yc": 1.0},
            [_sp(q_crane_t=100, col_step=6, crane_mode="Режим 1-6К")],
        )
        res78 = calculate(
            {"L_build": 60, "Q_snow": 2.1, "Q_dust": 0, "Q_tech": 0, "yc": 1.0},
            [_sp(q_crane_t=100, col_step=6, crane_mode="Режим 7-8К")],
        )
        pb16 = res16["подкрановые_балки"]["масса_общая_т_М1"]
        pb78 = res78["подкрановые_балки"]["масса_общая_т_М1"]
        assert pb78 / pb16 == pytest.approx(1.80, rel=0.01)


class TestEtalonBlok4CraneBeamM2:
    """Блок 4. Подкрановые балки М2 — эталон из таблицы CRANE_BEAM_T1 (методика, разд. 5.2).

    Контрольный пример: Q_кран=20 т, L_пб=6 м, Режим 7-8К, 1 кран.
      CRANE_BEAM_T1[6], Q=20т, 1 кран → 150 кг/м
      × коэф. 7-8К (1.80) → 270 кг/м
      На балку 6 м → 270 × 6 = 1620 кг
    """

    def test_crane_beam_t1_20t_6m_1crane(self):
        """CRANE_BEAM_T1: Q=20т, L=6м, 1 кран → 150 кг/м (из таблицы методики)."""
        kgm = get_crane_beam_kgm(20, 6, 1)
        assert kgm == pytest.approx(150, rel=0.01)

    def test_m2_with_78k_factor_270kgm(self):
        """С коэф. 7-8К (×1.80): 150 × 1.80 = 270 кг/м."""
        kgm = get_crane_beam_kgm(20, 6, 1)
        factor = CRANE_MODE_FACTOR_M2["Режим 7-8К"]
        assert kgm * factor == pytest.approx(270, rel=0.01)

    def test_m2_20t_6m_beam_total_1620kg(self):
        """Итого на 6 м балку: 270 × 6 = 1620 кг."""
        kgm = get_crane_beam_kgm(20, 6, 1)
        factor = CRANE_MODE_FACTOR_M2["Режим 7-8К"]
        assert kgm * factor * 6 == pytest.approx(1620, rel=0.01)

    def test_m2_2cranes_heavier_than_1crane(self):
        """2 крана дают большую нагрузку, чем 1 кран."""
        kgm1 = get_crane_beam_kgm(20, 6, 1)
        kgm2 = get_crane_beam_kgm(20, 6, 2)
        assert kgm2 > kgm1
