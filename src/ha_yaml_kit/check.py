"""Light checks for a Home Assistant automations file."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

MODES = ("single", "restart", "queued", "parallel")
_TRIGGER = ("trigger", "triggers")
_ACTION = ("action", "actions")


@dataclass(frozen=True)
class Issue:
    where: str
    message: str


class FileProblem(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def format_issue(path: str, issue: Issue) -> str:
    if issue.where:
        return f"{path}: {issue.where}: {issue.message}"
    return f"{path}: {issue.message}"


def check_text(text: str) -> list[Issue]:
    try:
        docs = list(yaml.safe_load_all(text))
    except yaml.YAMLError as exc:
        detail = str(exc).strip().splitlines()
        line = detail[0] if detail else "could not parse"
        return [Issue("", f"invalid YAML: {line}")]

    # A trailing "---" can leave an extra empty document. Ignore those.
    docs = [doc for doc in docs if doc is not None]
    if not docs:
        return [Issue("", "expected a list of automations")]
    if len(docs) > 1:
        return [Issue("", "expected a single YAML document")]
    return check_data(docs[0])


def check_data(data) -> list[Issue]:
    if not isinstance(data, list):
        return [Issue("", "expected a list of automations")]

    issues: list[Issue] = []
    seen: set[str] = set()
    for index, item in enumerate(data, start=1):
        where = f"item {index}"
        if not isinstance(item, dict):
            issues.append(Issue(where, "expected a mapping"))
            continue
        _check_name(item, "id", where, issues, seen)
        _check_alias(item, where, issues)
        _check_block(item, _TRIGGER, where, issues)
        _check_block(item, _ACTION, where, issues)
        _check_mode(item, where, issues)
        _check_values(item, where, issues)
    return issues


def check_path(path: Path | str) -> list[Issue]:
    raw = str(path)
    if raw == "-":
        return check_text(sys.stdin.read())

    file_path = Path(path)
    if not file_path.is_file():
        raise FileProblem("not a file")
    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise FileProblem("file is not valid UTF-8") from exc
    except OSError as exc:
        raise FileProblem(exc.strerror or "could not read file") from exc
    return check_text(text)


def _check_name(item: dict, key: str, where: str, issues: list[Issue], seen: set[str]) -> None:
    if key not in item:
        issues.append(Issue(where, f"missing {key}"))
        return
    value = item[key]
    if not isinstance(value, str):
        issues.append(Issue(where, f"{key} must be a string"))
        return
    if not value.strip():
        issues.append(Issue(where, f"{key} is empty"))
        return
    if value in seen:
        issues.append(Issue(where, f"duplicate id {value!r}"))
        return
    seen.add(value)


def _check_alias(item: dict, where: str, issues: list[Issue]) -> None:
    if "alias" not in item:
        issues.append(Issue(where, "missing alias"))
        return
    value = item["alias"]
    if not isinstance(value, str):
        issues.append(Issue(where, "alias must be a string"))
        return
    if not value.strip():
        issues.append(Issue(where, "alias is empty"))


def _check_block(item: dict, names: tuple[str, str], where: str, issues: list[Issue]) -> None:
    found = [name for name in names if name in item]
    if len(found) > 1:
        issues.append(Issue(where, f"has both {names[0]} and {names[1]}"))
        return
    if not found:
        issues.append(Issue(where, f"missing {names[0]} or {names[1]}"))
        return

    key = found[0]
    value = item[key]
    if value is None or value == [] or value == {}:
        issues.append(Issue(where, f"{key} is empty"))
        return
    if isinstance(value, dict):
        return
    if isinstance(value, list):
        for index, entry in enumerate(value, start=1):
            if not isinstance(entry, dict):
                issues.append(Issue(where, f"{key} item {index} should be a mapping"))
        return
    issues.append(Issue(where, f"{key} should be a list or a mapping"))


def _check_mode(item: dict, where: str, issues: list[Issue]) -> None:
    if "mode" not in item:
        return
    mode = item["mode"]
    if mode not in MODES:
        allowed = ", ".join(MODES)
        issues.append(Issue(where, f"mode must be one of {allowed}"))


def _check_values(value, where: str, issues: list[Issue]) -> None:
    if isinstance(value, dict):
        for key, inner in value.items():
            if key in {"to", "from"} and isinstance(inner, bool):
                issues.append(
                    Issue(where, f"{key} is a boolean; quote it if you meant \"on\" or \"off\"")
                )
                continue
            if key in {"at", "for"} and isinstance(inner, int) and not isinstance(inner, bool):
                issues.append(Issue(where, f"{key} was read as a number; quote the time"))
                continue
            _check_values(inner, where, issues)
    elif isinstance(value, list):
        for inner in value:
            _check_values(inner, where, issues)
