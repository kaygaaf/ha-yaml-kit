import io
import sys

import yaml

from ha_yaml_kit.cli import main
from ha_yaml_kit.check import check_data


def test_check_quiet_when_ok(tmp_path, capsys):
    path = tmp_path / "automations.yaml"
    path.write_text(
        "- id: a\n  alias: A\n  triggers:\n    - platform: time\n      at: '07:00:00'\n"
        "  actions:\n    - service: light.turn_on\n      target:\n        entity_id: light.a\n",
        encoding="utf-8",
    )
    assert main(["check", str(path)]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_check_reports_problems(tmp_path, capsys):
    path = tmp_path / "automations.yaml"
    path.write_text("- alias: Nope\n", encoding="utf-8")
    assert main(["check", str(path)]) == 1
    out = capsys.readouterr().out
    assert "missing id" in out
    assert "missing trigger or triggers" in out
    assert str(path) in out


def test_check_missing_file(tmp_path, capsys):
    path = tmp_path / "nope.yaml"
    assert main(["check", str(path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "not a file" in captured.err


def test_check_stdin(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO("- id: a\n  alias: A\n  trigger: []\n  action: {}\n"),
    )
    assert main(["check", "-"]) == 1
    assert "trigger is empty" in capsys.readouterr().out


def test_template_motion_light_stdout(capsys):
    rc = main(
        [
            "template",
            "motion-light",
            "--motion",
            "binary_sensor.hall_motion",
            "--light",
            "light.hall",
            "--minutes",
            "5",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    data = yaml.safe_load(out)
    assert check_data(data) == []
    assert data[0]["action"][1]["delay"]["minutes"] == 5


def test_template_schedule_stdout(capsys):
    rc = main(
        [
            "template",
            "schedule",
            "--entity",
            "switch.porch",
            "--on",
            "18:00",
            "--off",
            "23:00",
            "--id",
            "porch_light",
        ]
    )
    assert rc == 0
    data = yaml.safe_load(capsys.readouterr().out)
    assert [item["id"] for item in data] == ["porch_light_on", "porch_light_off"]
    assert check_data(data) == []


def test_template_bad_entity(capsys):
    rc = main(
        [
            "template",
            "motion-light",
            "--motion",
            "not an entity",
            "--light",
            "light.hall",
        ]
    )
    assert rc == 2
    assert "should look like" in capsys.readouterr().err
