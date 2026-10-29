"""Dump YAML in the shape Home Assistant files usually have."""

from __future__ import annotations

import re

import yaml

# YAML 1.1 (what Home Assistant parses) treats these words as booleans,
# and unquoted HH:MM:SS as a base-60 number.
_BOOL_WORD = re.compile(r"^(?:y|n|yes|no|true|false|on|off|~|null)$", re.IGNORECASE)
_TIME = re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?$")


class Dumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

    def increase_indent(self, flow=False, indentless=False):
        # Indent sequences under their key, same as typical HA YAML.
        return super().increase_indent(flow, False)


def _represent_str(dumper: yaml.Dumper, data: str):
    style = None
    if data == "" or _BOOL_WORD.match(data) or _TIME.match(data):
        style = '"'
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


Dumper.add_representer(str, _represent_str)


def dump(data) -> str:
    text = yaml.dump(
        data,
        Dumper=Dumper,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=1000,
    )
    if not text.endswith("\n"):
        text += "\n"
    return text
