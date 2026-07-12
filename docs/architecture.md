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

## Priority Engine

Every widget reports how important its information is *right now*:

| importance | meaning | examples |
|---|---|---|
| 100 | warning, act immediately | door locked but open |
| 70–90 | relevant today | waste today, birthday, door open, weather |
| 40–60 | relevant soon | appointment in 2 days, open window, empty house |
| 10–30 | background info | power draw, everything closed, who is home |

The renderer keeps the `MAX_ITEMS` (5) most important visible items and displays them ordered by `priority`. Widgets that return `None` (nothing relevant, sensor unavailable) never occupy a slot.

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
