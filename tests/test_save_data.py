"""Test harness for save data load/save."""
from __future__ import annotations

from pathlib import Path

from systems.save_data import SaveData


def test_save_data_roundtrip(tmp_path):
    path = tmp_path / "save.json"
    save = SaveData(path)
    save.add_coins(50)
    save.unlock_weapon("smg")
    save.set_stage_result("stage_city_01", 3, 1200)
    save2 = SaveData(path)
    assert save2.data["coins"] >= 50
    assert save2.get_weapon_unlocks()["smg"] is True
    assert save2.get_completed_stages()["stage_city_01"]["stars"] == 3
