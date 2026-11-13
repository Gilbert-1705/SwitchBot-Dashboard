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
WidgetManager ──> Widgets ──> DashboardItem ──> DashboardRenderer ──> SwitchBotAPI
     │                                               │
 widgets/config.py                             Priority Engine
 (typed dataclasses)                        (importance + visible)
```

- **WidgetManager** (`widgets/manager.py`) instantiates widgets from the typed configs in `widgets/config.py` (`WIDGET_TYPES` registry).
- **Widgets** (`widgets/*.py`) each render a single `DashboardItem` or `None` when they have nothing relevant to say. Widgets never talk to the display.
- **DashboardItem** (`dashboard/item.py`) carries `icon`, `value`, `priority` (display order), `importance` (situational relevance) and `visible`.
- **DashboardRenderer** (`dashboard/renderer.py`) implements the priority engine and layout.
- **Formatters** (`formatters/`) turn raw states into display strings, created via `FormatterFactory`.
- **SwitchBotAPI** (`api.py`) signs requests and sends the rendered line to the device (`customPage` command).

## Priority Engine 2.0

Every widget reports how important its information is *right now*. Since v2.0 the importance bands are official semantics (constants in `const.py`):

| band | meaning | examples |
|---|---|---|
| 100 (`IMPORTANCE_ALARM`) | warning, act immediately | door locked but open, laundry waiting 3 h |
| 60–99 (`IMPORTANCE_ALWAYS`) | always shown (within `max_items`) | weather, waste today, birthday |
| 21–59 | normal, competes for slots | appointment in 2 days, fresh done reminder |
| 0–20 (`IMPORTANCE_FILLER`) | background info, quiet days only | power draw, everything closed |

The renderer keeps the `max_items` (5) most important visible items and displays them ordered by `priority`. Widgets that return `None` (nothing relevant, sensor unavailable) never occupy a slot.

**Quiet mode:** filler items (≤ 20) never push the display beyond `quiet_max_items` (3). On a busy day they are displaced anyway; on a calm day the display stays calm — `🌡 21°C ☀   ●   🚪 Zu` instead of five slots of noise.

**Time-based importance:** information can get more urgent over time. `ramp.time_based_importance(last_changed, steps)` maps the elapsed time since a state change to an importance value — the appliance widget uses it for the done reminder (30 right away, 60 after 1 h, 100 after 3 h). The updater's periodic refresh re-renders every 15 minutes, so ramps take effect without state changes.

## Display constraints

The SwitchBot firmware wraps the transmitted line itself, pixel-based, preferring spaces. Consequences:

- Widgets are joined with `SEPARATOR` (three spaces) as preferred break positions.
- The renderer hard-caps each value at `MAX_VALUE_LENGTH` (14) characters.
- Widgets shorten semantically first: `join_names()` collapses lists ("Wohnen+2"), `shorten()` truncates with an ellipsis ("Max Muste…").
- Emoji support of the firmware varies; all icons are defined centrally in `icons.py` so they can be swapped easily.

## Adding a widget

1. Create `widgets/<name>.py` with a `BaseWidget` subclass; `render()` returns a `DashboardItem` or `None`.
2. If it needs configuration, add a dataclass in `widgets/config_models.py` and handle it in `widgets/manager.py`.
3. Register the class in `WIDGET_TYPES` and add an entry to `widgets/config.py`.
4. Choose importance values following the table above.
5. Add tests in `tests/` (Home Assistant is stubbed, no HA installation required).

## Services

- `switchbot_dashboard.preview` — render all widgets and send the result to the display
- `switchbot_dashboard.send_text` — send raw text
- `switchbot_dashboard.refresh` — reserved for event-driven refresh
