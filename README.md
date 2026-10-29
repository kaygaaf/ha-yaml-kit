# ha-yaml-kit

Helpers for Home Assistant automation YAML — templates, checks, less copy-paste.

Aimed at people who already run HA and want cleaner automations without fighting the UI every time.

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

Nothing printed means it looks fine. Problems are printed and the command exits 1. A missing path exits 2. Pass `-` to read stdin.

```
automations.yaml: item 2: missing alias
automations.yaml: item 3: duplicate id 'porch_on'
```

Home Assistant will invent an id and an alias if you leave them out. This still wants both, because automations without a name are a pain to find later.

`trigger` / `triggers` and `action` / `actions` both count. A single mapping is fine, and so is a list. An empty list (`[]`) is fine. A blank file is not. It still has to be a list. Don't put both `trigger` and `triggers` on the same automation.

A couple of YAML 1.1 surprises get flagged, because Home Assistant still parses YAML the old way:

- `to: on` and `from: off` are booleans unless you quote them (`"on"` / `"off"`)
- `at: 18:00:00` and `for: 00:01:00` are numbers unless you quote them

If you set `mode`, it has to be `single`, `restart`, `queued`, or `parallel`.

## Templates

Prints YAML on stdout. Paste the blocks into `automations.yaml`.

Motion turns a light on, then off after a few minutes. Mode is `restart`, so another trigger starts the timer over.

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

`--id` and `--alias` override the generated names. Minutes default to 5.

On at one time, off at another. This prints two automations. Lights, switches, fans, and input booleans use `domain.turn_on` / `turn_off`. Anything else uses `homeassistant.turn_on` / `turn_off`.

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
