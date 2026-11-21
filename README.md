# SwitchBot Dashboard

*[Deutsche Version](README.de.md)*

A Home Assistant custom integration that turns the SwitchBot Weather Station into a context-aware E-Ink dashboard.

Unlike classic dashboards that permanently show every available sensor, SwitchBot Dashboard displays only the information that is relevant *right now*. Walking past the display should answer three questions in seconds:

> Ist alles in Ordnung? Muss ich noch etwas tun? Gibt es heute etwas Wichtiges?

```
🌡 21°C ☀   ○ Wohnen   🚪 Auf   🗑 Rest Heute   🎂 Oma
```

And on a quiet day:

```
🌡 21°C ☀   ●   🚪 Zu
```

## Status

✅ Stable (v2.7.1) — see [CHANGELOG](CHANGELOG.md)

## How it works

Every widget reports two values with each render:

- **priority** — where the item appears in the line (display order)
- **importance** — how relevant the information is *at this moment*

The priority engine collects all visible items, keeps the five most important ones and renders them in their configured order. A locked-but-open door (importance 100) will always beat the current power draw (importance 10).

## Widgets

| Widget | Example | Shows |
|---|---|---|
| Weather | `🌡 21°C ☀` | Temperature + trend; calm against jitter, optional reference sensor against sun on the sensor |
| Entity | `P 380W` | Any entity with a formatter (power, number, …) |
| Door | `🚪 Zu` / `! Offen` | Smart lock + contact sensor combined: Zu, Auf, Offen, Warnung |
| Window | `○ Wohnen+Essen` / `○ Gekippt` | Open rooms by name (`mode="rooms"`) or compact state only (`mode="state"`), `●` when everything is closed |
| Waste | `🗑 Rest Morgen` | Next waste collection within 3 days |
| Calendar | `🎂 Oma`, `📅 Zahnarzt 2T` | Birthdays, appointments, holidays, vacation |
| Presence | `⌂ Jan+Anna` / `⌂ Leer` | Who is home; an empty house ranks higher |
| Fuel | `⛽ Tanken 1.65` | Tank level (% or liters) + refuel recommendation based on level and price thresholds |
| Appliance | `🧺 WM Fertig` / `🍽 GS Trocknen` | Washer, dryer, dishwasher: phase or remaining time while running, done reminder that grows louder; works with simple sensors and WashData (see [examples](docs/examples.md)) |
| Solar | `☀ 3.2kW` | PV production, hidden at night |
| Battery | `🔋 eBike 15%` | Any battery (PV storage, e-bike, …), important when low |
| EV | `🔌 64% lädt` | EV state of charge + charging status, reminder when low and unplugged |
| Alert | `! Regen rein` | Smart alerts: rules across multiple entities ("window open + rain > 70%"), triggers alarm mode |
| Threshold | `☁ CO₂ 1450` | Any numeric sensor, shown only while out of bounds (air quality, electricity price, humidity) |
| Status | `! NAS+VPN` | Shows only what is down: servers, VPN, services |
| Wallbox | `🔌 WB 7.4kW` | Charging point: power while charging, finished, error |
| Media | `♪ Bohemian Rhapsody` | Current title of a media player, only while playing |

## Installation

**HACS (recommended):** HACS → Integrations → ⋮ → Custom repositories → add `https://github.com/Gilbert-1705/SwitchBot-Dashboard` as *Integration*, then install and restart Home Assistant.

**Manual:** Copy `custom_components/switchbot_dashboard` into your Home Assistant `config/custom_components/` folder and restart.

## Configuration

The credentials (token, secret and device ID from the developer options of the SwitchBot app) go into YAML or the UI (Settings → Devices & Services); the widgets are configured in `configuration.yaml` — see the [full widget reference](docs/configuration.md):

```yaml
switchbot_dashboard:
  token: !secret switchbot_token
  secret: !secret switchbot_secret
  device_id: !secret switchbot_device_id
  max_items: 5
  widgets:
    - type: weather
    - type: waste
      entity: sensor.muellkalender
    - type: calendar
      entity: calendar.geburtstage
      icon: "🎂"
      days: 1
```

Ready-made setups (laundry reminder, dishwasher with WashData, virtual buttons) are in [docs/examples.md](docs/examples.md). Custom widgets and formatters can be registered via the [widget API](docs/configuration.md#custom-widgets). Services: `switchbot_dashboard.refresh` renders and sends right away, `switchbot_dashboard.preview` renders and sends the dashboard, `switchbot_dashboard.reload` applies a changed YAML block without a restart, `switchbot_dashboard.send_text` sends raw text.

## Display notes

The display does not redraw as soon as a new text arrives: it fetches the custom page on its own schedule (the fixed times set in the SwitchBot app, otherwise about every three hours). Short events - a window tilted for ten minutes - may never reach the screen; the dashboard is built for the state you see when walking past.

The SwitchBot firmware wraps the line itself (pixel-based, at spaces). The renderer therefore separates widgets with three spaces, sends the spaces inside a widget as no-break spaces so an icon never ends up apart from its text, and caps every widget text at 14 characters (the media widget gets 20); widgets additionally shorten their own output (`Wohnen+2`, `Max Muste…`).

## Development

`sensor.switchbot_dashboard` mirrors the rendered line inside Home Assistant (attributes `sent_to_device`, `rendered_at`). With `dry_run: true` the SwitchBot API is never called — widget development without a device and without the rate limit. The architecture is described in [docs/architecture.md](docs/architecture.md).

## Tests

```
for t in custom_components/switchbot_dashboard/tests/test_*.py; do python3 "$t"; done
```

Every test file also runs on its own. The tests stub Home Assistant and run without an HA installation.

## Roadmap

Done and open items: [TODO.md](TODO.md). Next up: screenshots from the real display, a list of the emojis the firmware renders, the first GitHub release and the official HACS store listing.

## License

MIT — see [LICENSE](LICENSE). You may use, change and redistribute the code, also commercially, as long as the copyright notice and the license text are kept. The software comes without any warranty.

SwitchBot is a trademark of its respective owner. This project is an independent community integration and is not affiliated with or endorsed by SwitchBot or Home Assistant.
