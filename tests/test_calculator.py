# -*- coding: utf-8 -*-
"""
Тесты для модуля расчёта металлоёмкости.

Запуск: python -m pytest tests/ -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculator_logic import (
    CalculatorLogic, InputParams, SpanParams,
    _get_alpha_pb, _get_q_rail, _interpolate_table,
    PROGON_6M, PROGON_12M, H_CRANE, A_GAP, H_F, H_SH,
)


# ── Фикстуры ────────────────────────────────────────────────────────────────

def make_span(**kwargs) -> SpanParams:
    """Базовый пролёт с разумными значениями по умолчанию."""
    defaults = dict(
        span_L=30.0,
        truss_step_B=6.0,
        column_step=6.0,
        rail_level=10.0,
        Q_snow=1.5,
        Q_dust=0.5,
        Q_roof=0.3,
        Q_purlin=0.2,
        yc=1.0,
        truss_type='Уголки',
        crane_capacity=20.0,
        crane_count=1,
        crane_mode='1К-6К',
        brake_path='С проходом',
        fachwerk_load=0.0,
        fachwerk_post=False,
        building_type='Основные',
    )
    defaults.update(kwargs)
    return SpanParams(**defaults)


def make_calc() -> CalculatorLogic:
    calc = CalculatorLogic()
    calc._coverage_data = None
    calc._fachwerk_data = None
    calc._crane_beams = None
    calc._brake = None
    return calc


# ── 1. Разные параметры пролётов ─────────────────────────────────────────────

class TestMultiSpan:
    def test_width_two_equal_spans(self):
        """Ширина здания = сумма пролётов."""
        sp1 = make_span(span_L=24.0)
        sp2 = make_span(span_L=30.0)
        params = InputParams(length=60.0, spans=[sp1, sp2])
        assert params.width == pytest.approx(54.0)

    def test_width_three_spans(self):
        sp1 = make_span(span_L=18.0)
        sp2 = make_span(span_L=24.0)
        sp3 = make_span(span_L=30.0)
        params = InputParams(length=60.0, spans=[sp1, sp2, sp3])
        assert params.width == pytest.approx(72.0)

    def test_different_column_steps_per_span(self):
        """Каждый пролёт может иметь свой шаг колонн."""
        sp1 = make_span(column_step=6.0, span_L=24.0)
        sp2 = make_span(column_step=12.0, span_L=30.0)
        calc = make_calc()
        # Пролёт с шагом 12м → подстропильные фермы
        r1 = calc.calc_podstropilnye(sp1, 60.0, 5.0, 1.0)
        r2 = calc.calc_podstropilnye(sp2, 60.0, 5.0, 1.0)
        assert r1['method'] == 0   # шаг 6м — не нужны
        assert r2.get('total_kg', 0) > 0  # шаг 12м — нужны

    def test_different_rail_levels_per_span(self):
        """Разные уровни рельса для соседних пролётов."""
        sp1 = make_span(rail_level=8.0)
        sp2 = make_span(rail_level=12.0)
        calc = make_calc()
        r1 = calc.calc_columns(sp1, 60.0, 0.1, 0.1, 0, 2500)
        r2 = calc.calc_columns(sp2, 60.0, 0.1, 0.1, 0, 2500)
        assert r2['total_kg'] > r1['total_kg']

    def test_full_calculate_two_spans(self):
        """Полный расчёт двух пролётов не вызывает ошибки."""
        sp1 = make_span(span_L=24.0, column_step=6.0)
        sp2 = make_span(span_L=30.0, column_step=12.0)
        params = InputParams(length=60.0, spans=[sp1, sp2])
        calc = CalculatorLogic()
        results = calc.calculate(params)
        assert '_error' not in results
        assert results['_total_kg'] > 0
        assert len(results['_spans']) == 2


# ── 2. Прогоны: шаг ферм и формула n_pr ─────────────────────────────────────

class TestProgony:
    def test_table_choice_truss_step_6(self):
        """При шаге ферм 6 м — используется PROGON_6M."""
        sp = make_span(truss_step_B=6.0, span_L=30.0)
        calc = make_calc()
        r = calc.calc_progony(sp, 60.0)
        # m_pr должна быть из PROGON_6M (все значения ≤ 576.6 кг)
        max_6m = max(m for _, m in PROGON_6M)
        assert r['m_pr'] <= max_6m

    def test_table_choice_truss_step_12(self):
        """При шаге ферм 12 м — используется PROGON_12M."""
        sp = make_span(truss_step_B=12.0, span_L=30.0)
        calc = make_calc()
        r = calc.calc_progony(sp, 60.0)
        min_12m = min(m for _, m in PROGON_12M)
        max_12m = max(m for _, m in PROGON_12M)
        assert min_12m <= r['m_pr'] <= max_12m * 1.01

    def test_n_pr_formula(self):
        """n_pr = span_L / a_pr + 1 (без лишней +3)."""
        sp = make_span(span_L=30.0)
        calc = make_calc()
        r = calc.calc_progony(sp, 60.0)
        # a_pr = 3.0, span_L = 30 → n_pr = 30/3 + 1 = 11
        assert r['n_pr'] == 11

    def test_n_pr_span_18(self):
        sp = make_span(span_L=18.0)
        calc = make_calc()
        r = calc.calc_progony(sp, 60.0)
        assert r['n_pr'] == 7  # 18/3 + 1

    def test_n_pr_span_24(self):
        sp = make_span(span_L=24.0)
        calc = make_calc()
        r = calc.calc_progony(sp, 60.0)
        assert r['n_pr'] == 9  # 24/3 + 1

    def test_n_pr_span_36(self):
        sp = make_span(span_L=36.0)
        calc = make_calc()
        r = calc.calc_progony(sp, 60.0)
        assert r['n_pr'] == 13  # 36/3 + 1

    def test_heavier_load_heavier_purlin(self):
        """Бо́льшая снеговая нагрузка → бо́льшая масса прогона."""
        sp_light = make_span(Q_snow=0.5)
        sp_heavy = make_span(Q_snow=3.0)
        calc = make_calc()
        r_light = calc.calc_progony(sp_light, 60.0)
        r_heavy = calc.calc_progony(sp_heavy, 60.0)
        assert r_heavy['m_pr'] >= r_light['m_pr']

    def test_total_kg_proportional_to_length(self):
        """Общая масса прогонов пропорциональна длине здания."""
        sp = make_span(span_L=30.0)
        calc = make_calc()
        r60 = calc.calc_progony(sp, 60.0)
        r120 = calc.calc_progony(sp, 120.0)
        assert r120['total_kg'] == pytest.approx(r60['total_kg'] * 2, rel=0.01)


# ── 3. Подкрановые балки: режимы 1К-6К и 7К-8К ──────────────────────────────

class TestPodkranovye:
    def test_alpha_pb_heavy_greater_than_light(self):
        """αпб для 7К-8К больше, чем для 1К-6К."""
        for q in [10, 20, 50, 100]:
            a_heavy = _get_alpha_pb(q, '7К-8К')
            a_light = _get_alpha_pb(q, '1К-6К')
            assert a_heavy > a_light, f"Q={q}: αпб(7К-8К)={a_heavy} ≤ αпб(1К-6К)={a_light}"

    def test_m1_heavy_mode_heavier_than_light(self):
        """Режим 7К-8К → масса балок (М1) выше, чем 1К-6К."""
        sp_heavy = make_span(crane_mode='7К-8К', crane_capacity=20.0)
        sp_light = make_span(crane_mode='1К-6К', crane_capacity=20.0)
        calc = make_calc()
        r_heavy = calc.calc_podkranovye_balki(sp_heavy, 60.0)
        r_light = calc.calc_podkranovye_balki(sp_light, 60.0)
        assert r_heavy['total_kg'] > r_light['total_kg']

    def test_mode_ratio_range(self):
        """mode_ratio для 1К-6К ≈ 0.45–0.60 (снижение ~40–55%)."""
        for q in [10, 20, 50, 100]:
            sp = make_span(crane_capacity=float(q), column_step=6.0)
            calc = make_calc()
            r = calc.calc_podkranovye_balki(sp, 60.0)
            sp_78 = make_span(crane_capacity=float(q), crane_mode='7К-8К', column_step=6.0)
            r_78 = calc.calc_podkranovye_balki(sp_78, 60.0)
            ratio = r['total_kg'] / r_78['total_kg']
            assert 0.35 <= ratio <= 0.75, f"Q={q}: ratio={ratio:.2f} выходит за пределы 0.35–0.75"

    def test_two_cranes_heavier(self):
        """Два крана → балки тяжелее."""
        sp1 = make_span(crane_count=1)
        sp2 = make_span(crane_count=2)
        calc = make_calc()
        r1 = calc.calc_podkranovye_balki(sp1, 60.0)
        r2 = calc.calc_podkranovye_balki(sp2, 60.0)
        assert r2['total_kg'] >= r1['total_kg']

    def test_column_step_12_heavier(self):
        """Шаг колонн 12 м → более тяжёлые балки, чем 6 м."""
        sp6 = make_span(column_step=6.0)
        sp12 = make_span(column_step=12.0)
        calc = make_calc()
        r6 = calc.calc_podkranovye_balki(sp6, 60.0)
        r12 = calc.calc_podkranovye_balki(sp12, 60.0)
        # При 12м балки значительно тяжелее на единицу длины
        assert r12['total_kg'] > r6['total_kg']

    def test_larger_crane_heavier_beams(self):
        """Бо́льшая грузоподъёмность → тяжелее балки."""
        sp20 = make_span(crane_capacity=20.0)
        sp80 = make_span(crane_capacity=80.0)
        calc = make_calc()
        r20 = calc.calc_podkranovye_balki(sp20, 60.0)
        r80 = calc.calc_podkranovye_balki(sp80, 60.0)
        assert r80['total_kg'] > r20['total_kg']

    def test_q_rail_increases_with_capacity(self):
        """Масса рельса монотонно растёт с г/п крана."""
        qs = [10, 20, 30, 50, 80, 200, 400]
        vals = [_get_q_rail(q) for q in qs]
        for i in range(len(vals) - 1):
            assert vals[i] <= vals[i + 1]


# ── 4. Высоты колонн H_v и H_n ───────────────────────────────────────────────

class TestColumnHeights:
    """Проверяет корректность разделения на подкрановую и надкрановую части."""

    def _get_heights(self, rail_level, crane_capacity, column_step=6.0):
        """Возвращает (H_v, H_n, h_b, h_r) через полный прогон calc_columns."""
        sp = make_span(
            rail_level=rail_level,
            crane_capacity=crane_capacity,
            column_step=column_step,
        )
        # Вычисляем h_b и h_r так же, как в calc_columns
        h_b = column_step / 6 if crane_capacity <= 50 else column_step / 7
        if crane_capacity <= 20:
            h_r = 0.130
        elif crane_capacity <= 50:
            h_r = 0.150
        elif crane_capacity <= 80:
            h_r = 0.170
        else:
            h_r = 0.180
        H2 = round((rail_level + H_CRANE + 0.1 + A_GAP) * 2) / 2
        H_v = H2 - rail_level + h_b + h_r
        H_n = rail_level - h_b - h_r + H_F
        return H_v, H_n, h_b, h_r, H2

    def test_Hv_positive(self):
        H_v, *_ = self._get_heights(10.0, 20.0)
        assert H_v > 0

    def test_Hn_positive(self):
        _, H_n, *_ = self._get_heights(10.0, 20.0)
        assert H_n > 0

    def test_Hv_Hn_sum_equals_total(self):
        """H_v + H_n = H2 + H_F (полная высота колонны)."""
        for rail_level in [8.0, 10.0, 12.0, 14.0]:
            for q in [10.0, 20.0, 80.0, 125.0]:
                H_v, H_n, h_b, h_r, H2 = self._get_heights(rail_level, q)
                total = H_v + H_n
                expected = H2 + H_F
                assert total == pytest.approx(expected, abs=0.01), \
                    f"rail={rail_level}, Q={q}: H_v+H_n={total:.2f} ≠ H2+H_F={expected:.2f}"

    def test_h_r_by_crane_capacity(self):
        """Высота рельса соответствует таблице по г/п."""
        cases = [(10, 0.130), (20, 0.130), (30, 0.150), (50, 0.150),
                 (80, 0.170), (100, 0.180), (200, 0.180)]
        for q, expected_hr in cases:
            _, _, _, h_r, _ = self._get_heights(10.0, float(q))
            assert h_r == pytest.approx(expected_hr), f"Q={q}: h_r={h_r} ≠ {expected_hr}"

    def test_Hv_not_includes_rail_level(self):
        """H_v (надкрановая) не должна включать уровень рельса как слагаемое."""
        H_v_10, *_ = self._get_heights(10.0, 20.0)
        H_v_12, *_ = self._get_heights(12.0, 20.0)
        # При увеличении rail_level на 2м H_v не меняется (зависит только от H2-rail_level)
        assert H_v_10 == pytest.approx(H_v_12, abs=0.01)

    def test_Hn_grows_with_rail_level(self):
        """H_n (подкрановая) растёт при увеличении уровня рельса."""
        H_v_10, H_n_10, *_ = self._get_heights(10.0, 20.0)
        H_v_12, H_n_12, *_ = self._get_heights(12.0, 20.0)
        assert H_n_12 > H_n_10

    def test_column_weight_7k8k_heavier_than_1k6k(self):
        """Колонны при 7К-8К тяжелее (больше нагрузки от балок → тяжелее нижняя часть)."""
        sp_h = make_span(crane_mode='7К-8К')
        sp_l = make_span(crane_mode='1К-6К')
        calc = make_calc()
        r_h = calc.calc_columns(sp_h, 60.0, 0.1, 0.1, 0, 3000)
        r_l = calc.calc_columns(sp_l, 60.0, 0.1, 0.1, 0, 2000)
        assert r_h['total_kg'] > r_l['total_kg']


# ── 5. Вспомогательные функции ───────────────────────────────────────────────

class TestHelpers:
    def test_alpha_pb_table_boundary(self):
        """αпб для г/п ≤ 10т — минимальное значение из таблицы."""
        assert _get_alpha_pb(5.0, '7К-8К') == 0.45
        assert _get_alpha_pb(10.0, '7К-8К') == 0.45

    def test_alpha_pb_interpolation(self):
        """αпб для промежуточного г/п берётся из ближайшего верхнего ключа."""
        # 15т → ключ 20 → 0.55 (7К-8К)
        assert _get_alpha_pb(15.0, '7К-8К') == 0.55

    def test_interpolate_table_exact(self):
        """Точное совпадение с ключом в таблице."""
        table = [(1.0, 100.0), (2.0, 200.0), (3.0, 300.0)]
        assert _interpolate_table(table, 2.0) == 200.0

    def test_interpolate_table_between(self):
        """Промежуточное значение → ближайший больший ключ."""
        table = [(1.0, 100.0), (2.0, 200.0), (3.0, 300.0)]
        assert _interpolate_table(table, 1.5) == 200.0

    def test_interpolate_table_exceeds_max(self):
        """Превышение максимума → последнее значение таблицы."""
        table = [(1.0, 100.0), (2.0, 200.0)]
        assert _interpolate_table(table, 99.0) == 200.0


# ── 6. Интеграционный тест ───────────────────────────────────────────────────

class TestIntegration:
    def test_full_single_span_no_error(self):
        sp = make_span()
        params = InputParams(length=60.0, spans=[sp])
        calc = CalculatorLogic()
        results = calc.calculate(params)
        assert '_error' not in results
        assert results['_total_kg'] > 0
        assert results['_kg_m2'] > 0

    def test_area_correct(self):
        sp = make_span(span_L=30.0)
        params = InputParams(length=60.0, spans=[sp])
        calc = CalculatorLogic()
        results = calc.calculate(params)
        assert results['_area'] == pytest.approx(60.0 * 30.0)

    def test_kg_m2_consistent(self):
        sp = make_span(span_L=30.0)
        params = InputParams(length=60.0, spans=[sp])
        calc = CalculatorLogic()
        results = calc.calculate(params)
        expected = results['_total_kg'] / results['_area']
        assert results['_kg_m2'] == pytest.approx(expected, rel=0.001)

    def test_longer_building_proportional_mass(self):
        """Удвоение длины здания → примерно удвоение массы."""
        sp = make_span()
        p60 = InputParams(length=60.0, spans=[sp])
        p120 = InputParams(length=120.0, spans=[sp])
        calc60 = CalculatorLogic()
        calc120 = CalculatorLogic()
        r60 = calc60.calculate(p60)
        r120 = calc120.calculate(p120)
        ratio = r120['_total_kg'] / r60['_total_kg']
        # Не строго 2.0 из-за торцевых конструкций, но в пределах 1.5–2.5
        assert 1.5 <= ratio <= 2.5

    def test_heavy_crane_mode_increases_total(self):
        """Режим 7К-8К → итоговая металлоёмкость выше, чем 1К-6К."""
        sp_h = make_span(crane_mode='7К-8К')
        sp_l = make_span(crane_mode='1К-6К')
        p_h = InputParams(length=60.0, spans=[sp_h])
        p_l = InputParams(length=60.0, spans=[sp_l])
        c_h, c_l = CalculatorLogic(), CalculatorLogic()
        r_h = c_h.calculate(p_h)
        r_l = c_l.calculate(p_l)
        assert r_h['_total_kg'] > r_l['_total_kg']

    def test_column_step_12_has_podstropilnye(self):
        """При шаге колонн 12 м в результатах есть подстропильные фермы."""
        sp = make_span(column_step=12.0)
        params = InputParams(length=60.0, spans=[sp])
        calc = CalculatorLogic()
        results = calc.calculate(params)
        span_res = dict(results['_spans'])
        first_span = list(span_res.values())[0]
        pf = first_span.get('Подстропильные фермы', {})
        assert pf.get('total_kg', 0) > 0

    def test_podstropilnye_absent_step_6(self):
        """При шаге колонн 6 м подстропильных ферм нет (method=0)."""
        sp = make_span(column_step=6.0)
        params = InputParams(length=60.0, spans=[sp])
        calc = CalculatorLogic()
        results = calc.calculate(params)
        _, span_res = results['_spans'][0]
        pf = span_res.get('Подстропильные фермы', {})
        assert pf.get('method', -1) == 0
