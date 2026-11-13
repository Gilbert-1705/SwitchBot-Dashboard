# Configuration

Widgets can be configured in two ways:

1. **YAML** in `configuration.yaml` (recommended) — no code changes needed
2. **Python** in `custom_components/switchbot_dashboard/widgets/config.py` — used as fallback when no `widgets:` block is present

## Full example

The credentials can alternatively be configured via the UI
(Settings → Devices & Services → Add Integration → SwitchBot Dashboard);
the `widgets:` block stays in YAML either way.

```yaml
switchbot_dashboard:
  token: !secret switchbot_token
  secret: !secret switchbot_secret
  device_id: !secret switchbot_device_id
  max_items: 5          # optional, Anzahl gleichzeitig sichtbarer Widgets
  auto_refresh: true    # optional, event-getriebener Auto-Refresh
  dry_run: false        # optional, true = nur lokale Preview, kein API-Call
  quiet_max_items: 3    # optional, max. Items an ruhigen Tagen

  widgets:
    - type: weather
      temperature_entity: sensor.aussen_temperatur
      trend_entity: sensor.wettertrend

    - type: entity
      entity: sensor.stromverbrauch
      icon: "P"
      formatter: power
      priority: 200

    - type: window
      entities:
        binary_sensor.balkontuer_1: Balkon 1
        binary_sensor.balkontuer_2: Balkon 2
      mode: state        # "rooms" (Namen) oder "state" (Offen/Gekippt)
      priority: 250

    - type: door
      lock_entity: lock.haustuer
      contact_entity: binary_sensor.haustuer_kontakt
      priority: 300

    - type: waste
      entity: sensor.muellkalender
      days: 3
      priority: 400

    - type: calendar
      entity: calendar.geburtstage
      icon: "🎂"
      days: 1
      priority: 500

    - type: presence
      entities:
        person.jan: Jan
        person.anna: Anna
      priority: 600

    - type: fuel
      level_entity: sensor.auto_tank
      price_entity: sensor.spritpreis
      min_level: 20      # in "unit"
      max_price: 1.75    # EUR/l
      unit: "%"          # "%" oder "l"
      priority: 610

    - type: appliance
      name: WM
      running_entity: sensor.waschmaschine_status
      done_entity: input_boolean.waschmaschine_fertig
      icon: "🧺"
      priority: 700
```

## Auto refresh

With `auto_refresh: true` (default) the dashboard watches every
configured entity and updates the display automatically: state
changes are debounced for 5 s, the display is only contacted when the
rendered line actually changed, and API calls are rate-limited to one
per minute (SwitchBot recommendation). A periodic refresh every
15 minutes catches date rollovers (waste, calendar). The
`switchbot_dashboard.refresh` service forces an immediate update and
bypasses the rate limit; `preview` renders and sends once without the
updater.

## Local preview (development)

The integration mirrors every rendered line to a local entity,
`sensor.switchbot_dashboard` — state is the display text, attributes
show `sent_to_device` and `rendered_at`. Add it to any Lovelace card
or watch it in Developer Tools → States to iterate on widgets without
looking at the e-paper.

With `dry_run: true` the SwitchBot API is never called: the dashboard
only updates the preview entity. Ideal for development — no device,
no rate limit, full priority-engine behavior.

## Display constraints (official)

Per SwitchBot's custom-page documentation:

- Payload limit is ~**300 bytes UTF-8** (emojis take 4 bytes). The
  integration caps outgoing text automatically and logs when the API
  rejects a payload (`statusCode 190`).
- **Line breaks are not supported** (`\n`, `<br>` are ignored) — the
  firmware wraps at spaces, which is why widgets are joined with
  triple spaces.
- **Simple emojis only**: skin-tone modifiers and ZWJ combinations may
  not render. Recommended set includes ✅❌📅🌤🏠💧⚡📬🐱🎂📊💪.
  All icons live in `icons.py` and are easy to swap.
- Sending an **empty string clears** the custom page (the dashboard
  does this when no widget has anything to show).
- The custom page is **not the default screen** — swipe to it on the
  device once; refreshes can take a few seconds.
- API rate: max one call per minute (enforced by the updater).

Configuration errors are reported in the Home Assistant log with widget position, type and field, e.g. `Widget 3 (window): unknown option 'entitys'. Available: entities, mode, priority`.

## Widget reference

All widgets accept these base options:

- `priority` — display order (lower = further left)
- `group` — widgets sharing a group render at most one item, the
  most important one. Example: door, window and an alert as group
  `haus` show `⚠ Haus` instead of three separate lines.
- `boost` — day context: time windows that raise or lower the
  importance. Windows may wrap over midnight; multiple active
  windows add up; boosts never reach alarm level (capped at 99).

```yaml
- type: waste
  entity: sensor.muellkalender
  boost:
    - between: ["06:00", "09:00"]   # waste matters in the morning
      add: 20

- type: appliance
  name: WM
  running_entity: sensor.wm_status
  done_entity: input_boolean.wm_fertig
  boost:
    - between: ["22:00", "06:00"]   # don't nag at night
      add: -30
```

### weather

| Option | Required | Default | Description |
|---|---|---|---|
| `temperature_entity` | no | built-in | Temperature sensor |
| `trend_entity` | no | built-in | Trend sensor (`sunny`, `cloudy`, `rainy`) |
| `icon` | no | `🌡` | Icon |

Always important (importance 90). Renders `🌡 21°C ☀`.

### entity

| Option | Required | Default | Description |
|---|---|---|---|
| `entity` | **yes** | – | Any sensor |
| `icon` | **yes** | – | Icon |
| `formatter` | no | raw value | `power`, `number` or custom |
| `importance` | no | 10 | Situational relevance |

### door

| Option | Required | Default | Description |
|---|---|---|---|
| `lock_entity` | no | built-in | Smart lock |
| `contact_entity` | no | built-in | Door contact sensor |

States: `🚪 Zu` (20), `🚪 Auf` (60), `🚪 Offen` (75), `! Offen` when locked but open (100).

### window

| Option | Required | Default | Description |
|---|---|---|---|
| `entities` | **yes** | – | Mapping `entity_id: Name` |
| `mode` | no | `rooms` | `rooms` (names) or `state` (Offen/Gekippt) |

Understands `on`/`open`/`Offen` and `Gekippt` (case-insensitive). Tilted-only ranks low — leaving the house with tilted windows is fine.

### waste

| Option | Required | Default | Description |
|---|---|---|---|
| `entity` | no | built-in | Calendar sensor with date attributes |
| `days` | no | 3 | Lookahead in days |

Renders `🗑 Rest Heute`, `🗑 Gelb Morgen`, `🗑 Papier 3T`.

### calendar

| Option | Required | Default | Description |
|---|---|---|---|
| `entity` | **yes** | – | HA calendar entity |
| `icon` | **yes** | – | e.g. `🎂 📅 ★ ✈` |
| `days` | no | 3 | Lookahead in days |

Renders `🎂 Oma` (today), `🎂 Oma Morgen`, `🎂 Oma 3T`. One widget per calendar.

### presence

| Option | Required | Default | Description |
|---|---|---|---|
| `entities` | **yes** | – | Mapping `person entity: Name` |

Renders `⌂ Jan+Anna` (importance 15) or `⌂ Leer` (45).

### fuel

| Option | Required | Default | Description |
|---|---|---|---|
| `level_entity` | **yes** | – | Tank level sensor |
| `price_entity` | **yes** | – | Fuel price sensor (EUR/l) |
| `min_level` | no | 20 | Level threshold (in `unit`) |
| `max_price` | no | 1.75 | Price threshold |
| `unit` | no | `%` | `%` or `l` |
| `max_price_entity` | no | – | Reference price sensor; replaces `max_price` while it has a value |
| `price_margin` | no | 0 | Allowed surcharge on the reference price (EUR/l) |

Renders `⛽ Tanken 1.65` (85), `⛽ 12%` (65), `⛽ 1.65` (40) or nothing.

A fixed `max_price` ages badly: fuel prices swing by tens of cents
within a day and the level drifts over weeks. Point `max_price_entity`
at a statistics helper instead (Settings → Helpers → Statistics, source:
the price sensor, characteristic: minimum, max age: 7 days) and set
`price_margin: 0.03` - "good" then means "at most 3 cents above the
lowest price of the last 7 days".

### appliance

| Option | Required | Default | Description |
|---|---|---|---|
| `name` | **yes** | – | Short label, e.g. `WM`, `TR`, `GS` |
| `running_entity` | **yes** | – | Status sensor (see states below) |
| `done_entity` | no | – | `input_boolean` reminder flag |
| `remaining_entity` | no | – | Remaining time in minutes |
| `phase_entity` | no | – | Current phase, shown while running |
| `icon` | no | `🧺` | Icon |

Understood states (case-insensitive): running = `on`, `run`,
`running`, `starting`, `ending`; paused = `pause`, `paused`,
`user_paused`; waiting = `delay_wait`; done = `finished`, `clean`,
`anti_wrinkle`; failed = `interrupted`, `force_stopped`. Everything
else (`off`, `idle`, `stop`, ...) hides the widget.

While running the widget shows the phase if known (`🍽 GS Trocknen`,
a trailing temperature like "Reinigen 45" is stripped), otherwise
the remaining time rounded up to 5-minute steps (`🍽 GS 45min`, so
the e-paper does not refresh every minute), otherwise `läuft`.

The done reminder (`Fertig`) ramps 30 → 60 (1 h) → 95 (3 h). It can
come from the status entity itself (a done state such as WashData's
`clean`) or from the manual `done_entity` flag — both work
together. See [examples.md](examples.md) for the automations and the
WashData setup.

### solar

| Option | Required | Default | Description |
|---|---|---|---|
| `entity` | **yes** | – | PV production sensor (W) |
| `min_power` | no | 50 | Threshold (W) below which the widget hides |
| `icon` | no | `☀` | Icon |

Renders `☀ 3.2kW` (importance 15). Hidden at night.

### battery

| Option | Required | Default | Description |
|---|---|---|---|
| `entity` | **yes** | – | Battery level sensor (%) |
| `name` | no | – | Short label, e.g. `eBike`, `Speicher` |
| `min_level` | no | 20 | Below this the battery becomes important (65) |
| `show_always` | no | `false` | Show as background info (15) even when ok |
| `icon` | no | `🔋` | Icon |

One instance per battery — PV storage, e-bike, vacuum, …

### ev

| Option | Required | Default | Description |
|---|---|---|---|
| `soc_entity` | **yes** | – | State-of-charge sensor (%) |
| `charging_entity` | no | – | Charging sensor (`on`/`charging`) |
| `name` | no | – | Short label, e.g. `EV` |
| `min_level` | no | 20 | Reminder threshold when not charging |
| `show_always` | no | `false` | Show as background info even when ok |
| `icon` | no | `🔌` | Icon |

Renders `🔌 EV 64% lädt` (30), `🔌 EV 12%` when low and unplugged (65).

### alert

Smart alerts combine states that Home Assistant knows but never
brings together. All conditions must hold (AND); build OR by
configuring several alerts.

```yaml
- type: alert
  name: Regen rein
  conditions:
    - entity: binary_sensor.fenster_wohnen
      state: Offen
    - entity: sensor.regen_wahrscheinlichkeit
      above: 70

- type: alert
  name: Tür offen!
  conditions:
    - entity: binary_sensor.haustuer
      state: "on"
      duration: 600        # seconds in this state
    - entity: person.jan
      not_state: home
```

| Option | Required | Default | Description |
|---|---|---|---|
| `name` | **yes** | – | Display text |
| `conditions` | **yes** | – | List of conditions (see below) |
| `icon` | no | `!` | Icon |
| `importance` | no | 100 | 100 triggers alarm mode |

Condition keys: `entity` (required) plus at least one of `state`
(string or list, case-insensitive), `not_state`, `above`, `below`,
`duration` (seconds in the current state). Unknown or unavailable
entities make a condition false — alerts never fire on missing data.

**Alarm mode:** as soon as any item reaches importance 100, only
alarms and always-band items (≥ 60) are displayed; everything else
is displaced so the warning stands out.

## Custom widgets

```python
from custom_components.switchbot_dashboard.widgets.base import (
    BaseWidget, DashboardItem,
)
from custom_components.switchbot_dashboard.widgets.config_models import (
    WidgetConfig,
)
from custom_components.switchbot_dashboard.widgets.registry import (
    register_widget_type,
)
from dataclasses import dataclass


@dataclass(slots=True)
class PlantWidgetConfig(WidgetConfig):
    entity: str = ""


class PlantWidget(BaseWidget):

    def __init__(self, hass, entity, priority=800):
        super().__init__(hass)
        self.entity = entity
        self.priority = priority

    def render(self):
        state = self.hass.states.get(self.entity)
        if state is None or float(state.state) > 30:
            return None
        return DashboardItem(
            icon="🌱",
            value="Gießen",
            priority=self.priority,
            importance=55,
        )


register_widget_type(
    "plant", PlantWidget, PlantWidgetConfig,
    required=("entity",),
)
```

Rules of thumb: return `None` whenever there is nothing relevant to say; config dataclass fields must match the constructor parameters; pick `importance` following the scale in [architecture.md](architecture.md).

## Custom formatters

```python
from custom_components.switchbot_dashboard.formatters.base import (
    BaseFormatter,
)
from custom_components.switchbot_dashboard.formatters.factory import (
    FormatterFactory,
)


class EuroFormatter(BaseFormatter):
    def format(self, value):
        return f"{float(value):.2f}€"


FormatterFactory.register("euro", EuroFormatter)
```

Then use `formatter: euro` in any `entity` widget.
