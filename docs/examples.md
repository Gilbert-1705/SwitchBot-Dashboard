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
        entity_id: binary_sensor.waschmaschine_laeuft
        from: "on"
        to: "off"
        for: "00:02:00"   # Entprellen (Schleudern-Pausen)
    action:
      - service: input_boolean.turn_on
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

Behavior: `🧺 WM Fertig` (importance 80) while the flag is set,
`🧺 WM läuft` (importance 15) while running, hidden otherwise.
