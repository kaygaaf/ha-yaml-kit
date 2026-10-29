import yaml

from ha_yaml_kit.check import check_data
from ha_yaml_kit.templates import motion_light, schedule
from ha_yaml_kit.yamlutil import dump


def test_motion_light_shape_and_check():
    data = motion_light(motion="binary_sensor.hall_motion", light="light.hall", minutes=5)
    assert check_data(data) == []
    auto = data[0]
    assert auto["id"] == "hall_motion"
    assert auto["alias"] == "Hall motion light"
    assert auto["mode"] == "restart"
    assert auto["trigger"][0]["to"] == "on"
    assert auto["action"][1] == {"delay": {"minutes": 5}}
    assert auto["action"][0]["service"] == "light.turn_on"
    assert auto["action"][2]["service"] == "light.turn_off"

    text = dump(data)
    assert "trigger:\n    - platform: state\n" in text
    assert 'to: "on"' in text
    assert "&" not in text
    loaded = yaml.safe_load(text)
    assert loaded[0]["trigger"][0]["to"] == "on"


def test_motion_light_custom_names():
    data = motion_light(
        motion="binary_sensor.kitchen",
        light="light.kitchen_main",
        minutes=12,
        automation_id="kitchen-night",
        alias="Kitchen at night",
    )
    assert data[0]["id"] == "kitchen-night"
    assert data[0]["alias"] == "Kitchen at night"
    assert data[0]["action"][1]["delay"]["minutes"] == 12


def test_motion_light_rejects_bad_input():
    import pytest

    with pytest.raises(ValueError):
        motion_light(motion="Hall Motion", light="light.hall")
    with pytest.raises(ValueError):
        motion_light(motion="binary_sensor.hall", light="switch.hall")
    with pytest.raises(ValueError):
        motion_light(motion="binary_sensor.hall", light="light.hall", minutes=0)


def test_schedule_two_automations():
    data = schedule(entity="switch.porch", on="18:00", off="23:30:00")
    assert check_data(data) == []
    assert [item["id"] for item in data] == ["porch_on", "porch_off"]
    assert data[0]["trigger"][0]["at"] == "18:00:00"
    assert data[1]["trigger"][0]["at"] == "23:30:00"
    assert data[0]["action"][0]["service"] == "switch.turn_on"
    assert data[1]["action"][0]["service"] == "switch.turn_off"
    assert data[0]["alias"] == "Porch on"
    assert data[1]["alias"] == "Porch off"

    text = dump(data)
    assert 'at: "18:00:00"' in text
    loaded = yaml.safe_load(text)
    assert loaded[0]["trigger"][0]["at"] == "18:00:00"


def test_schedule_other_domain_and_alias():
    data = schedule(
        entity="media_player.den",
        on="7:05",
        off="22:00",
        automation_id="den",
        alias="Den speaker",
    )
    assert data[0]["id"] == "den_on"
    assert data[0]["alias"] == "Den speaker on"
    assert data[0]["action"][0]["service"] == "homeassistant.turn_on"
    assert data[0]["trigger"][0]["at"] == "07:05:00"


def test_schedule_rejects_same_time():
    import pytest

    with pytest.raises(ValueError):
        schedule(entity="switch.porch", on="18:00", off="18:00:00")
