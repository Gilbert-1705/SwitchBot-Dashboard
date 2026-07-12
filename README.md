# SwitchBot Dashboard

A Home Assistant custom integration that turns the SwitchBot Weather Station into a context-aware E-Ink dashboard.

Unlike classic dashboards that permanently show every available sensor, SwitchBot Dashboard displays only the information that is relevant *right now*. Walking past the display should answer three questions in seconds:

> Ist alles in Ordnung? Muss ich noch etwas tun? Gibt es heute etwas Wichtiges?

```
🌡 21°C ☀   ○ Wohnen   🚪 Auf   🗑 Rest Heute   🎂 Oma
```

And on a quiet day:

```
🌡 21°C ☀   P 280W   ●   🚪 Zu
```

## Status

🚧 In development (v0.3.0) — Sprint 4 of 6, see [CHANGELOG](CHANGELOG.md)

## How it works

Every widget reports two values with each render:

- **priority** — where the item appears in the line (display order)
- **importance** — how relevant the information is *at this moment*

The priority engine collects all visible items, keeps the five most important ones and renders them in their configured order. A locked-but-open door (importance 100) will always beat the current power draw (importance 10).

## Widgets

| Widget | Example | Shows |
|---|---|---|
| Weather | `🌡 21°C ☀` | Temperature + trend |
| Entity | `P 380W` | Any entity with a formatter (power, number, …) |
| Door | `🚪 Zu` / `! Offen` | Smart lock + contact sensor combined: Zu, Auf, Offen, Warnung |
| Window | `○ Wohnen+Essen` / `○ Gekippt` | Open rooms by name (`mode="rooms"`) or compact state only (`mode="state"`), `●` when everything is closed |
| Waste | `🗑 Rest Morgen` | Next waste collection within 3 days |
| Calendar | `🎂 Oma`, `📅 Zahnarzt 2T` | Birthdays, appointments, holidays, vacation |
| Presence | `⌂ Jan+Anna` / `⌂ Leer` | Who is home; an empty house ranks higher |
| Fuel | `⛽ Tanken 1.65` | Tank level (% or liters) + refuel recommendation based on level and price thresholds |
| Appliance | `🧺 WM Fertig` | Washer/dryer finished, until manually reset (see [examples](docs/examples.md)) |

## Configuration

Widgets are configured as typed dataclasses in `custom_components/switchbot_dashboard/widgets/config.py`; entity IDs live in `custom_components/switchbot_dashboard/config/entities.py`. The integration itself is configured via YAML:

```yaml
switchbot_dashboard:
  token: !secret switchbot_token
  secret: !secret switchbot_secret
  device_id: !secret switchbot_device_id
```

Services: `switchbot_dashboard.preview` renders and sends the dashboard, `switchbot_dashboard.send_text` sends raw text.

## Display notes

The SwitchBot firmware wraps the line itself (pixel-based, preferring spaces). The renderer therefore separates widgets with three spaces as break hints and caps every widget text at 14 characters; widgets additionally shorten their own output (`Wohnen+2`, `Max Muste…`).

## Tests

```
python3 custom_components/switchbot_dashboard/tests/test_sprint3.py
python3 custom_components/switchbot_dashboard/tests/test_sprint4.py
```

The tests stub Home Assistant and run without an HA installation.

## Roadmap

- Sprint 5: simplified YAML configuration, validation, custom widget API
- Sprint 6: HACS release, GitHub Actions, documentation, v1.0
