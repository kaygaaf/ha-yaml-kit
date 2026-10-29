"""CLI: ha-yaml-kit check, ha-yaml-kit template."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ha_yaml_kit.check import FileProblem, check_path, format_issue
from ha_yaml_kit.templates import motion_light, schedule
from ha_yaml_kit.yamlutil import dump


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ha-yaml-kit",
        description="Helpers for Home Assistant automation YAML.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    check = sub.add_parser("check", help="check an automations YAML file")
    check.add_argument("path", type=Path, help="path to a YAML file, or - for stdin")

    template = sub.add_parser("template", help="print an automation template")
    templates = template.add_subparsers(dest="name", required=True)

    motion = templates.add_parser(
        "motion-light",
        help="turn a light on with motion, off after N minutes",
    )
    motion.add_argument("--motion", required=True, help="motion entity, e.g. binary_sensor.hall_motion")
    motion.add_argument("--light", required=True, help="light entity, e.g. light.hall")
    motion.add_argument("--minutes", type=int, default=5, help="minutes before turn-off (default: 5)")
    motion.add_argument("--id", dest="automation_id", help="automation id (default: from the light name)")
    motion.add_argument("--alias", help="automation alias")

    sched = templates.add_parser(
        "schedule",
        help="turn an entity on at one time and off at another",
    )
    sched.add_argument("--entity", required=True, help="entity id, e.g. switch.porch")
    sched.add_argument("--on", required=True, help="turn-on time, HH:MM or HH:MM:SS")
    sched.add_argument("--off", required=True, help="turn-off time, HH:MM or HH:MM:SS")
    sched.add_argument("--id", dest="automation_id", help="id prefix (writes <id>_on and <id>_off)")
    sched.add_argument("--alias", help="alias prefix (writes '<alias> on' and '<alias> off')")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.cmd == "check":
            return _cmd_check(args.path)
        if args.cmd == "template":
            return _cmd_template(args)
    except ValueError as exc:
        print(f"ha-yaml-kit: {exc}", file=sys.stderr)
        return 2
    parser.error(f"unknown command {args.cmd}")
    return 2


def _cmd_check(path: Path) -> int:
    label = str(path)
    try:
        issues = check_path(path)
    except FileProblem as exc:
        print(f"{label}: {exc.message}", file=sys.stderr)
        return 2
    if not issues:
        return 0
    for issue in issues:
        print(format_issue(label, issue))
    return 1


def _cmd_template(args: argparse.Namespace) -> int:
    if args.name == "motion-light":
        data = motion_light(
            motion=args.motion,
            light=args.light,
            minutes=args.minutes,
            automation_id=args.automation_id,
            alias=args.alias,
        )
    elif args.name == "schedule":
        data = schedule(
            entity=args.entity,
            on=args.on,
            off=args.off,
            automation_id=args.automation_id,
            alias=args.alias,
        )
    else:
        raise ValueError(f"unknown template {args.name}")
    sys.stdout.write(dump(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
