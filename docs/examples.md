# Examples

## Laundry widget (Waschmaschine / Trockner)

The appliance widget shows `🧺 WM Fertig` until the laundry is actually
taken out. Since the appliance door state is not available, the
"done" flag is a manual `input_boolean` in Home Assistant.

### 1. Helper

```yaml
input_boolean:
  waschmaschine_fertig:
    name: Waschmaschine fertig
  trockner_fertig:
    name: Trockner fertig
```

### 2. Set the flag when the appliance finishes

Works with any "running" signal — a power-plug threshold template
sensor or an appliance integration:

```yaml
automation:
  - alias: "Waschmaschine: fertig markieren"
    trigger:
      - platform: state
        entity_id: sensor.waschmaschine_status
        from: "run"        # "pause" löst bewusst nicht aus
        to: "stop"
        for: "00:02:00"    # Entprellen
    action:
      - service: input_boolean.turn_on
        target:
          entity_id: input_boolean.waschmaschine_fertig
```

The widget itself understands `run`, `pause` and `stop` directly
(shown as "läuft", "Pause", hidden).

Optional: clear a stale flag automatically when a new cycle starts
(the widget already prefers "läuft" over "Fertig" on its own):

```yaml
  - alias: "Waschmaschine: Flag bei Neustart löschen"
    trigger:
      - platform: state
        entity_id: sensor.waschmaschine_status
        to: "run"
    action:
      - service: input_boolean.turn_off
        target:
          entity_id: input_boolean.waschmaschine_fertig
```

### 3. Reset the flag ("Wäsche geholt")

Any trigger works: a dashboard button, the SwitchBot app — or one of
the two custom buttons on the Weather Station itself.

#### Option A: Weather Station button via Matter (recommended)

With a Matter-enabled SwitchBot Hub, the two scene buttons of the
Weather Station are exposed as programmable Matter controls. Add the
hub to Home Assistant via the Matter integration, then:

```yaml
automation:
  - alias: "Wäsche geholt (Display-Button)"
    trigger:
      - platform: device
        # Matter-Button-Event der Wetterstation auswählen
        # (Geräte -> Weather Station -> Button 1)
    action:
      - service: input_boolean.turn_off
        target:
          entity_id:
            - input_boolean.waschmaschine_fertig
            - input_boolean.trockner_fertig
```

#### Option B: without Matter

The buttons can only trigger SwitchBot scenes, and the Weather
Station webhook does not report button presses. Workaround: let the
scene toggle a SwitchBot device (Plug Mini, Bot), watch that device
in Home Assistant via the `switchbot_cloud` integration and use its
state change as the trigger for the reset automation above.

### 4. Widget configuration

```python
ApplianceWidgetConfig(
    type="appliance",
    name="WM",
    running_entity="binary_sensor.waschmaschine_laeuft",
    done_entity="input_boolean.waschmaschine_fertig",
    icon=Icons.LAUNDRY,
    priority=700,
),
```

Behavior: `🧺 WM Fertig` while the flag is set (importance ramps
30 → 60 after 1 h → 95 after 3 h), `🧺 WM läuft` (importance 15)
while running, hidden otherwise.

## Dishwasher with WashData

WashData (a custom integration available via HACS) detects state
and phase of an appliance from its power consumption. The appliance
widget understands its state sensor directly:

```yaml
- type: appliance
  name: GS
  running_entity: sensor.geschirrspuler_zustand
  phase_entity: sensor.geschirrspuler_aktuelle_phase
  remaining_entity: sensor.geschirrspuler_verbleibende_zeit
  icon: "🍽"
  priority: 720
```

Result: `🍽 GS Trocknen` while running, `🍽 GS Fertig` when done,
`🍽 GS Abbruch` when a cycle was interrupted.

### Keeping the reminder until the dishwasher is unloaded

How long `Fertig` stays depends on WashData: the state sensor
reports `finished` only for a limited time and then returns to
`off` - unless the appliance stays in WashData's `clean` state until
"mark as unloaded" is pressed. If your reminder disappears too
early, add the manual done flag; it works together with the status
sensor:

```yaml
input_boolean:
  geschirrspueler_fertig:
    name: Geschirrspüler fertig

automation:
  - alias: "Geschirrspüler: fertig markieren"
    trigger:
      - platform: state
        entity_id: sensor.geschirrspuler_zustand
        to: "finished"
    action:
      - service: input_boolean.turn_on
        target:
          entity_id: input_boolean.geschirrspueler_fertig
```

and add `done_entity: input_boolean.geschirrspueler_fertig` to the
widget. Reset the flag like the laundry reminder above (display
button via Matter, app or dashboard). A new cycle overrides a stale
flag automatically.

## Virtual buttons as stand-ins for the display buttons

The two physical buttons of the Weather Station only reach Home
Assistant through a Matter-enabled SwitchBot hub. Until then (or
instead), two `input_button` helpers act as stand-ins: every reset
automation listens to a virtual button, and whatever ends up
pressing it - a dashboard card, a wall switch, later the real
display button - needs no further logic.

```yaml
input_button:
  display_taste_1:
    name: Display Taste 1
  display_taste_2:
    name: Display Taste 2

automation:
  - alias: "Display: Taste 1 – Wäsche ausgeräumt"
    trigger:
      - platform: state
        entity_id: input_button.display_taste_1
        not_from: unavailable
        not_to: [unavailable, unknown]
    action:
      - service: input_boolean.turn_off
        target:
          entity_id:
            - input_boolean.waschmaschine_fertig
            - input_boolean.trockner_fertig

  - alias: "Display: Taste 2 – Geschirrspüler ausgeräumt"
    trigger:
      - platform: state
        entity_id: input_button.display_taste_2
        not_from: unavailable
        not_to: [unavailable, unknown]
    action:
      - service: input_boolean.turn_off
        target:
          entity_id: input_boolean.geschirrspueler_fertig
```

Do not exclude `unknown` in `not_from`: a button that has never been
pressed is `unknown`, and its very first press must count.

The reminder ramp survives restarts: the integration keeps its own
record of when a flag was set instead of relying on `last_changed`,
which Home Assistant re-stamps on every restart.

