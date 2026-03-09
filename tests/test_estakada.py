# -*- coding: utf-8 -*-
"""
Тесты для модулей эстакад.

  estakada_pipe.py  — трубопроводные эстакады v3.2F
  estakada_elec.py  — электрокабельные эстакады и галереи v4.2F

Тестируем данные (CONFIGS), структурные инварианты и граничные условия.
GUI-классы (App) не тестируются — только чистые данные.

Запуск: python -m pytest tests/test_estakada.py -v
"""

import sys
import os

# conftest.py уже зарегистрировал заглушки customtkinter/tkinter.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from estakada_pipe import CONFIGS as PIPE_CONFIGS
from estakada_elec import CONFIGS as ELEC_CONFIGS


# ─────────────────────────────────────────────────────────────────────────────
#  Трубопроводные эстакады (estakada_pipe)
# ─────────────────────────────────────────────────────────────────────────────

class TestPipeConfigs:
    """Структурные проверки CONFIGS трубопроводных эстакад."""

    REQUIRED_KEYS = {"num", "max_pipes", "max_d_mm", "std_load", "svc_load", "kg_m",
                     "pipes_low", "pipes_high", "note"}

    def test_configs_not_empty(self):
        assert len(PIPE_CONFIGS) > 0

    def test_all_required_keys_present(self):
        for cfg in PIPE_CONFIGS:
            missing = self.REQUIRED_KEYS - set(cfg.keys())
            assert not missing, f"Конфиг #{cfg.get('num')}: отсутствуют ключи {missing}"

    def test_kg_m_positive(self):
        for cfg in PIPE_CONFIGS:
            assert cfg["kg_m"] > 0, f"Конфиг #{cfg['num']}: kg_m = {cfg['kg_m']}"

    def test_std_load_positive(self):
        for cfg in PIPE_CONFIGS:
            assert cfg["std_load"] > 0, f"Конфиг #{cfg['num']}: std_load = {cfg['std_load']}"

    def test_svc_load_non_negative(self):
        for cfg in PIPE_CONFIGS:
            assert cfg["svc_load"] >= 0, f"Конфиг #{cfg['num']}: svc_load = {cfg['svc_load']}"

    def test_max_pipes_positive(self):
        for cfg in PIPE_CONFIGS:
            assert cfg["max_pipes"] > 0, f"Конфиг #{cfg['num']}: max_pipes = {cfg['max_pipes']}"

    def test_max_d_mm_positive(self):
        for cfg in PIPE_CONFIGS:
            assert cfg["max_d_mm"] > 0, f"Конфиг #{cfg['num']}: max_d_mm = {cfg['max_d_mm']}"

    def test_pipes_low_le_pipes_high(self):
        for cfg in PIPE_CONFIGS:
            assert cfg["pipes_low"] <= cfg["pipes_high"], (
                f"Конфиг #{cfg['num']}: pipes_low > pipes_high"
            )

    def test_num_unique(self):
        nums = [c["num"] for c in PIPE_CONFIGS]
        assert len(nums) == len(set(nums)), "Дублирующиеся номера конфигов эстакад"

    def test_note_non_empty(self):
        for cfg in PIPE_CONFIGS:
            assert cfg["note"].strip(), f"Конфиг #{cfg['num']}: пустое примечание"

    def test_kg_m_in_reasonable_range(self):
        """Удельная масса: 0.1–5.0 т/м (реальные эстакады)."""
        for cfg in PIPE_CONFIGS:
            assert 0.1 <= cfg["kg_m"] <= 5.0, (
                f"Конфиг #{cfg['num']}: kg_m = {cfg['kg_m']} вне диапазона 0.1–5.0"
            )

    def test_heavier_load_heavier_structure(self):
        """Конфиги с бо́льшим std_load имеют бо́льший kg_m (в среднем)."""
        sorted_by_load = sorted(PIPE_CONFIGS, key=lambda c: c["std_load"])
        light = sorted_by_load[0]["kg_m"]
        heavy = sorted_by_load[-1]["kg_m"]
        assert heavy >= light, (
            f"Самая тяжёлая нагрузка ({sorted_by_load[-1]['std_load']}) "
            f"должна давать кг/м ≥ самой лёгкой ({sorted_by_load[0]['std_load']})"
        )

    def test_more_pipes_heavier_or_equal(self):
        """Бо́льшее max_pipes → кг/м не меньше (при схожих диаметрах)."""
        by_2pipes = [c for c in PIPE_CONFIGS if c["max_pipes"] == 2]
        by_6pipes = [c for c in PIPE_CONFIGS if c["max_pipes"] == 6]
        if by_2pipes and by_6pipes:
            avg_2 = sum(c["kg_m"] for c in by_2pipes) / len(by_2pipes)
            avg_6 = sum(c["kg_m"] for c in by_6pipes) / len(by_6pipes)
            assert avg_6 >= avg_2, (
                f"6-трубные конфиги (ср. {avg_6:.3f}) должны быть тяжелее "
                f"2-трубных (ср. {avg_2:.3f})"
            )


# ─────────────────────────────────────────────────────────────────────────────
#  Электрокабельные эстакады (estakada_elec)
# ─────────────────────────────────────────────────────────────────────────────

class TestElecConfigs:
    """Структурные проверки CONFIGS электрокабельных эстакад."""

    REQUIRED_KEYS = {"num", "kg_m", "std_load", "svc_load", "type_id", "note"}

    def test_configs_not_empty(self):
        assert len(ELEC_CONFIGS) > 0

    def test_all_required_keys_present(self):
        for cfg in ELEC_CONFIGS:
            missing = self.REQUIRED_KEYS - set(cfg.keys())
            assert not missing, f"Конфиг #{cfg.get('num')}: отсутствуют ключи {missing}"

    def test_kg_m_positive(self):
        for cfg in ELEC_CONFIGS:
            assert cfg["kg_m"] > 0, f"Конфиг #{cfg['num']}: kg_m = {cfg['kg_m']}"

    def test_std_load_positive(self):
        for cfg in ELEC_CONFIGS:
            assert cfg["std_load"] > 0, f"Конфиг #{cfg['num']}: std_load = {cfg['std_load']}"

    def test_svc_load_non_negative(self):
        for cfg in ELEC_CONFIGS:
            assert cfg["svc_load"] >= 0, f"Конфиг #{cfg['num']}: svc_load = {cfg['svc_load']}"

    def test_type_id_valid(self):
        """type_id: 0 = эстакада без прохода, 1 = галерея с проходом."""
        for cfg in ELEC_CONFIGS:
            assert cfg["type_id"] in (0, 1), (
                f"Конфиг #{cfg['num']}: type_id = {cfg['type_id']} (ожидается 0 или 1)"
            )

    def test_num_unique(self):
        nums = [c["num"] for c in ELEC_CONFIGS]
        assert len(nums) == len(set(nums)), "Дублирующиеся номера конфигов электроэстакад"

    def test_note_non_empty(self):
        for cfg in ELEC_CONFIGS:
            assert cfg["note"].strip(), f"Конфиг #{cfg['num']}: пустое примечание"

    def test_kg_m_in_reasonable_range(self):
        """Удельная масса: 0.05–2.0 т/м (электрокабельные легче трубопроводных)."""
        for cfg in ELEC_CONFIGS:
            assert 0.05 <= cfg["kg_m"] <= 2.0, (
                f"Конфиг #{cfg['num']}: kg_m = {cfg['kg_m']} вне диапазона 0.05–2.0"
            )

    def test_both_type_ids_present(self):
        """Должны быть конфиги и без прохода (0), и с проходом (1)."""
        ids = {c["type_id"] for c in ELEC_CONFIGS}
        assert 0 in ids, "Нет конфигов без прохода (type_id=0)"
        assert 1 in ids, "Нет конфигов с проходом (type_id=1)"

    def test_gallery_heavier_than_overpass(self):
        """Галерея с проходом в среднем тяжелее эстакады без прохода."""
        overpass = [c["kg_m"] for c in ELEC_CONFIGS if c["type_id"] == 0]
        gallery = [c["kg_m"] for c in ELEC_CONFIGS if c["type_id"] == 1]
        if overpass and gallery:
            avg_o = sum(overpass) / len(overpass)
            avg_g = sum(gallery) / len(gallery)
            assert avg_g >= avg_o, (
                f"Галереи (ср. {avg_g:.3f}) должны быть тяжелее эстакад (ср. {avg_o:.3f})"
            )

    def test_heavier_load_heavier_or_equal_per_type(self):
        """Внутри каждого type_id: бо́льший std_load → kg_m не меньше."""
        for type_id in (0, 1):
            cfgs = sorted(
                [c for c in ELEC_CONFIGS if c["type_id"] == type_id],
                key=lambda c: c["std_load"],
            )
            if len(cfgs) >= 2:
                for i in range(len(cfgs) - 1):
                    assert cfgs[i]["kg_m"] <= cfgs[i + 1]["kg_m"], (
                        f"type_id={type_id}: конфиг {cfgs[i]['num']} "
                        f"(load={cfgs[i]['std_load']}, kg_m={cfgs[i]['kg_m']}) "
                        f"тяжелее следующего {cfgs[i+1]['num']} "
                        f"(load={cfgs[i+1]['std_load']}, kg_m={cfgs[i+1]['kg_m']})"
                    )
