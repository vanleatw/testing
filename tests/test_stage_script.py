"""Minimal test harness for stage script parsing."""
from __future__ import annotations

from pathlib import Path

from systems.stage_script import StageScript


def test_stage_script_parses_example(tmp_path):
    sample = {
        "id": "stage_test",
        "zone": "City",
        "background": "city",
        "timeline": [
            {"time": 1.0, "action": "spawn", "params": {"type": "grunt"}},
            {"time": 3.0, "action": "powerup", "params": {"kind": "rapid"}},
        ],
    }
    path = tmp_path / "stage.json"
    path.write_text(__import__("json").dumps(sample))
    script = StageScript.from_json(path)
    assert script.stage_id == "stage_test"
    assert len(list(script.iter_events())) == 2
