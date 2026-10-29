"""A few automations people end up rewriting by hand."""

from __future__ import annotations

import re

_ENTITY = re.compile(r"^[a-z][a-z0-9_]*\.[a-z0-9_]+$")
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
_DIRECT_TURN = {"light", "switch", "fan", "input_boolean"}


def motion_light(
    *,
    motion: str,
    light: str,
    minutes: int = 5,
    automation_id: str | None = None,
    alias: str | None = None,
) -> list[dict]:
    """Turn a light on when motion trips, then off after ``minutes``.

    ``mode: restart`` so a new trigger starts the timer over.
    """
    _entity(motion, "motion")
    _entity(light, "light")
    if not light.startswith("light."):
        raise ValueError("light should be a light entity (light.something)")
    if isinstance(minutes, bool) or not isinstance(minutes, int) or minutes < 1:
        raise ValueError("minutes must be a positive integer")

    return [
        {
            "id": _auto_id(automation_id, f"{_object(light)}_motion"),
            "alias": _clean_alias(alias, f"{_phrase(light)} motion light"),
            "trigger": [
                {
                    "platform": "state",
                    "entity_id": motion,
                    "to": "on",
                }
            ],
            "action": [
                _service("light.turn_on", light),
                {"delay": {"minutes": minutes}},
                _service("light.turn_off", light),
            ],
            "mode": "restart",
        }
    ]


def schedule(
    *,
    entity: str,
    on: str,
    off: str,
    automation_id: str | None = None,
    alias: str | None = None,
) -> list[dict]:
    """Two automations: turn ``entity`` on at one time and off at another."""
    _entity(entity, "entity")
    on_at = _time(on)
    off_at = _time(off)
    if on_at == off_at:
        raise ValueError("on and off times are the same")

    base = _auto_id(automation_id, _object(entity))
    name = _clean_alias(alias, _phrase(entity))
    on_alias = f"{name} on"
    off_alias = f"{name} off"

    domain = entity.split(".", 1)[0]
    verb_domain = domain if domain in _DIRECT_TURN else "homeassistant"
    return [
        {
            "id": f"{base}_on",
            "alias": on_alias,
            "trigger": [{"platform": "time", "at": on_at}],
            "action": [_service(f"{verb_domain}.turn_on", entity)],
            "mode": "single",
        },
        {
            "id": f"{base}_off",
            "alias": off_alias,
            "trigger": [{"platform": "time", "at": off_at}],
            "action": [_service(f"{verb_domain}.turn_off", entity)],
            "mode": "single",
        },
    ]


def _service(service: str, entity: str) -> dict:
    return {
        "service": service,
        "target": {"entity_id": entity},
    }


def _entity(value: str, label: str) -> None:
    if not isinstance(value, str) or not _ENTITY.fullmatch(value):
        example = {
            "motion": "binary_sensor.hall_motion",
            "light": "light.hall",
            "entity": "switch.porch",
        }.get(label, "light.kitchen")
        raise ValueError(f"{label} should look like {example}")


def _auto_id(given: str | None, default: str) -> str:
    if given is None:
        value = default if _ID.fullmatch(default) else f"auto_{default}"
    else:
        value = given
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError("id should start with a letter and use letters, numbers, _ or -")
    return value


def _clean_alias(alias: str | None, default: str) -> str:
    if alias is None:
        return default
    cleaned = alias.strip()
    if not cleaned:
        raise ValueError("alias is empty")
    return cleaned


def _object(entity_id: str) -> str:
    return entity_id.split(".", 1)[1]


def _phrase(entity_id: str) -> str:
    words = _object(entity_id).replace("_", " ")
    return words[:1].upper() + words[1:]


def _time(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("time should look like 18:00 or 18:00:00")
    match = re.fullmatch(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", value.strip())
    if not match:
        raise ValueError("time should look like 18:00 or 18:00:00")
    hour = int(match.group(1))
    minute = int(match.group(2))
    second = int(match.group(3) or 0)
    if hour > 23 or minute > 59 or second > 59:
        raise ValueError("time should look like 18:00 or 18:00:00")
    return f"{hour:02d}:{minute:02d}:{second:02d}"
