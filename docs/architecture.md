# Architecture

## Philosophy

The dashboard does not show as many sensors as possible — it shows exactly the information that is relevant at this moment. Context-aware prioritization is the guiding principle for every design decision.

## Goals

- Modular widget system
- Home Assistant first
- Reusable renderer
- Event driven refresh
- HACS compatible

## Core Components

```
YAML / options ──> Settings ──> WidgetManager ──> Widgets ──> DashboardItem
                                                                  │
SwitchBotAPI <── DashboardUpdater <── render_dashboard <── DashboardRenderer
                 (events, debounce,                        (priority engine)
                  rate limit, retry)
```

- **Config entry and widget editor** (`config_flow.py`, `widget_forms.py`): credentials in the config entry, options in its options flow, every widget as a config subentry of type `widget` whose data is one item of the YAML `widgets:` list. The forms are derived from the config dataclasses; a YAML block with credentials is imported once.
- **Settings** (`settings.py`) validates the YAML block and merges the options of a config entry; `config/schema.py` turns the `widgets:` list into the typed dataclasses of `widgets/config_models.py`.
- **Widget registry** (`widgets/registry.py`) maps a type name to widget class, config class, required fields and an optional validator (`register_widget_type`).
- **WidgetManager** (`widgets/manager.py`) builds the widgets generically: every config field is passed to the constructor, `group` and `boost` are attached for the pipeline.
- **Widgets** (`widgets/*.py`) each render a single `DashboardItem` or `None` when they have nothing relevant to say. Widgets never talk to the display; display texts come from `i18n.py` (`self.t(key)`).
- **DashboardItem** (`dashboard/item.py`) carries `icon`, `value`, `priority` (display order), `importance` (situational relevance), `visible`, `group` and an optional `max_length`.
- **DashboardRenderer** (`dashboard/renderer.py`) implements the priority engine and layout; `render.py` applies groups and time-of-day boosts.
- **DashboardUpdater** (`updater.py`) listens to every configured entity, debounces changes (5 s), sends only changed text, respects the 60 s rate limit and retries after a refused or failed send.
- **SinceTracker** (`tracker.py`) remembers since when an entity holds its state, across restarts (`.storage/switchbot_dashboard.since`).
- **Formatters** (`formatters/`) turn raw states into display strings, created via `FormatterFactory`.
- **SwitchBotAPI** (`api.py`) signs requests and sends the rendered line to the device (`customPage` command), with a 15 s timeout; network errors become a regular failed result.

## Priority Engine 2.0

Every widget reports how important its information is *right now*. Since v2.0 the importance bands are official semantics (constants in `const.py`):

| band | meaning | examples |
|---|---|---|
| 100 (`IMPORTANCE_ALARM`) | warning, act immediately | door locked but open, smart alert, server down |
| 60–99 (`IMPORTANCE_ALWAYS`) | always shown (within `max_items`) | weather, waste today, birthday, laundry waiting 1 h+ |
| 21–59 | normal, competes for slots | appointment in 2 days, fresh done reminder |
| 0–20 (`IMPORTANCE_FILLER`) | background info, quiet days only | power draw, everything closed |

The renderer keeps the `max_items` (5) most important visible items and displays them ordered by `priority`. Widgets that return `None` (nothing relevant, sensor unavailable) never occupy a slot.

**Quiet mode:** filler items (≤ 20) never push the display beyond `quiet_max_items` (3). On a busy day they are displaced anyway; on a calm day the display stays calm — `🌡 21°C ☀   ●   🚪 Zu` instead of five slots of noise.

**Time-based importance:** information can get more urgent over time. `ramp.time_based_importance(last_changed, steps)` maps the elapsed time since a state change to an importance value — the appliance widget uses it for the done reminder (30 right away, 60 after 1 h, 95 after 3 h). The updater's periodic refresh re-renders every 15 minutes, so ramps take effect without state changes.

## Display constraints

The SwitchBot firmware wraps the transmitted line itself, pixel-based, preferring spaces. Consequences:

- Widgets are joined with `SEPARATOR` (three spaces) as preferred break positions.
- The renderer hard-caps each value at `MAX_VALUE_LENGTH` (14) characters;
  an item may ask for its own limit (`DashboardItem.max_length`, used by
  the media widget).
- Widgets shorten semantically first: `join_names()` collapses lists ("Wohnen+2"), `shorten()` truncates with an ellipsis ("Max Muste…").
- Emoji support of the firmware varies; all icons are defined centrally in `icons.py` so they can be swapped easily.

## Adding a widget

1. Create `widgets/<name>.py` with a `BaseWidget` subclass; `render()` returns a `DashboardItem` or `None`.
2. Add a config dataclass in `widgets/config_models.py` whose fields mirror the constructor parameters.
3. Register it in `widgets/registry.py` with `register_widget_type(name, widget_cls, config_cls, required=..., validator=...)`. The manager and the YAML validation need no further code.
4. Choose importance values following the table above; texts the widget prints itself go into `i18n.py`.
5. Add tests in `tests/` (Home Assistant is stubbed, no HA installation required).

## Services

- `switchbot_dashboard.refresh` — render and send right away, bypassing the rate limit
- `switchbot_dashboard.preview` — render all widgets and send the result to the display
- `switchbot_dashboard.reload` — re-read the YAML block and apply it without a restart
- `switchbot_dashboard.send_text` — send raw text
