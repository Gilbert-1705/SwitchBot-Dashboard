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

Configuration errors are reported in the Home Assistant log with widget position, type and field, e.g. `Widget 3 (window): unknown option 'entitys'. Available: entities, mode, priority`.

## Widget reference

All widgets accept `priority` (display order, lower = further left).

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

Renders `⛽ Tanken 1.65` (85), `⛽ 12%` (65), `⛽ 1.65` (40) or nothing.

### appliance

| Option | Required | Default | Description |
|---|---|---|---|
| `name` | **yes** | – | Short label, e.g. `WM`, `TR` |
| `running_entity` | **yes** | – | Status sensor (`run`/`pause`/`stop`) |
| `done_entity` | **yes** | – | `input_boolean` reminder flag |
| `icon` | no | `🧺` | Icon |

See [examples.md](examples.md) for the automations.

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
