import textwrap

import pytest

from ha_yaml_kit.check import FileProblem, check_data, check_path, check_text


def _automation(**overrides):
    data = {
        "id": "hall_motion",
        "alias": "Hall motion light",
        "trigger": [
            {
                "platform": "state",
                "entity_id": "binary_sensor.hall_motion",
                "to": "on",
            }
        ],
        "action": [
            {
                "service": "light.turn_on",
                "target": {"entity_id": "light.hall"},
            }
        ],
    }
    data.update(overrides)
    return data


def test_valid_list_is_clean():
    assert check_data([_automation()]) == []


def test_empty_list_is_clean():
    assert check_data([]) == []


def test_modern_key_names():
    item = _automation()
    item["triggers"] = item.pop("trigger")
    item["actions"] = item.pop("action")
    assert check_data([item]) == []


def test_single_mapping_trigger_is_ok():
    item = _automation(trigger={"platform": "state", "entity_id": "binary_sensor.hall_motion", "to": "on"})
    assert check_data([item]) == []


def test_missing_required_keys():
    messages = [issue.message for issue in check_data([{"mode": "single"}])]
    assert "missing id" in messages
    assert "missing alias" in messages
    assert "missing trigger or triggers" in messages
    assert "missing action or actions" in messages


def test_not_a_list():
    issues = check_data({"id": "x"})
    assert issues[0].message == "expected a list of automations"


def test_item_not_a_mapping():
    issues = check_data(["nope"])
    assert issues[0].where == "item 1"
    assert issues[0].message == "expected a mapping"


def test_duplicate_id():
    issues = check_data([_automation(), _automation()])
    assert any("duplicate id 'hall_motion'" in issue.message for issue in issues)


def test_bad_mode_and_empty_trigger():
    issues = check_data([_automation(trigger=[], mode="sometimes")])
    messages = [issue.message for issue in issues]
    assert "trigger is empty" in messages
    assert "mode must be one of single, restart, queued, parallel" in messages


def test_both_trigger_styles():
    item = _automation()
    item["triggers"] = item["trigger"]
    issues = check_data([item])
    assert any("both trigger and triggers" in issue.message for issue in issues)


def test_unquoted_on_and_time():
    text = textwrap.dedent(
        """
        - id: porch
          alias: Porch
          trigger:
            - platform: state
              entity_id: binary_sensor.porch
              to: on
            - platform: time
              at: 18:00:00
          action:
            - service: switch.turn_on
              target:
                entity_id: switch.porch
        """
    )
    messages = [issue.message for issue in check_text(text)]
    assert any("to is a boolean" in message for message in messages)
    assert any("at was read as a number" in message for message in messages)


def test_quoted_on_passes():
    text = textwrap.dedent(
        """
        - id: porch
          alias: Porch
          trigger:
            - platform: time
              at: "18:00:00"
          action:
            - service: switch.turn_on
              target:
                entity_id: switch.porch
        """
    )
    assert check_text(text) == []


def test_invalid_yaml():
    issues = check_text(":\n  - [")
    assert issues[0].message.startswith("invalid YAML:")


def test_two_documents():
    issues = check_text("[]\n---\n[]\n")
    assert issues[0].message == "expected a single YAML document"


def test_comments_only():
    issues = check_text("# nothing yet\n")
    assert issues[0].message == "expected a list of automations"


def test_empty_mapping_block():
    issues = check_data([_automation(trigger={}, action={})])
    messages = [issue.message for issue in issues]
    assert "trigger is empty" in messages
    assert "action is empty" in messages


def test_id_must_be_string():
    issues = check_data([_automation(id=3)])
    assert any(issue.message == "id must be a string" for issue in issues)


def test_check_path_roundtrip(tmp_path):
    path = tmp_path / "automations.yaml"
    path.write_text(
        "- id: a\n  alias: A\n  trigger:\n    platform: event\n    event_type: test\n"
        "  action:\n    service: light.turn_on\n    target:\n      entity_id: light.a\n",
        encoding="utf-8",
    )
    assert check_path(path) == []


def test_missing_file(tmp_path):
    with pytest.raises(FileProblem):
        check_path(tmp_path / "missing.yaml")
