# ha-yaml-kit

Helpers for Home Assistant automation YAML. Templates, checks, less copy-paste.

You already run HA. This is for editing automations in a file instead of clicking around the UI.

## Install

Python 3.9 or newer. From a checkout of this repo:

```bash
pip install .
```

`pip install -e ".[dev]"` also installs pytest, if you want to run the tests.

## Check a file

`automations.yaml` should be a list. Each automation needs an `id`, an `alias`, a trigger, and an action.

```bash
ha-yaml-kit check automations.yaml
```

No output means it looks fine. Problems print to stdout and the command exits 1. A missing path exits 2. Pass `-` to read stdin.

```
automations.yaml: item 2: missing alias
automations.yaml: item 3: duplicate id 'porch_on'
```

HA will make up an id and an alias if you leave them out. This check still asks for both. Automations with no name are a pain to find later.

`trigger` or `triggers` both work. Same for `action` and `actions`. One mapping is fine. A list is fine. An empty list (`[]`) is fine. A blank file still has to be a list. Don't put `trigger` and `triggers` on the same automation.

It also warns about two YAML 1.1 things. HA still parses YAML the old way.

- `to: on` and `from: off` turn into booleans. Quote them (`"on"`, `"off"`).
- `at: 18:00:00` and `for: 00:01:00` turn into numbers. Quote the time.

If you set `mode`, use `single`, `restart`, `queued`, or `parallel`.

## Templates

These print YAML. Paste the blocks into `automations.yaml`.

Motion turns a light on, then off after a few minutes. `mode` is `restart`, so a new trigger starts the timer over.

```bash
ha-yaml-kit template motion-light \
  --motion binary_sensor.hall_motion \
  --light light.hall \
  --minutes 5
```

```yaml
- id: hall_motion
  alias: Hall motion light
  trigger:
    - platform: state
      entity_id: binary_sensor.hall_motion
      to: "on"
  action:
    - service: light.turn_on
      target:
        entity_id: light.hall
    - delay:
        minutes: 5
    - service: light.turn_off
      target:
        entity_id: light.hall
  mode: restart
```

Use `--id` and `--alias` if you want your own names. Minutes default to 5.

On at one time, off at another. This prints two automations. Lights, switches, fans, and input_booleans use `domain.turn_on` / `turn_off`. Anything else uses `homeassistant.turn_on` / `turn_off`.

```bash
ha-yaml-kit template schedule \
  --entity switch.porch \
  --on 18:00 \
  --off 23:00
```

```yaml
- id: porch_on
  alias: Porch on
  trigger:
    - platform: time
      at: "18:00:00"
  action:
    - service: switch.turn_on
      target:
        entity_id: switch.porch
  mode: single
- id: porch_off
  alias: Porch off
  trigger:
    - platform: time
      at: "23:00:00"
  action:
    - service: switch.turn_off
      target:
        entity_id: switch.porch
  mode: single
```

`--id porch_light` writes `porch_light_on` and `porch_light_off`. `--alias "Porch light"` writes "Porch light on" and "Porch light off". Times can be `HH:MM` or `HH:MM:SS`.

`ha-yaml-kit template -h` lists the templates.

## Support

[ko-fi.com/kayorama](https://ko-fi.com/kayorama)
