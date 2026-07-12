# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog
and this project follows Semantic Versioning.

## [0.1.0] - 2026-07-05

### Added

- Initial dashboard renderer
- Modular widget architecture
- Weather widget
- Entity widget
- Door widget
- Formatter framework
- Preview service
- Config models
- Icon abstraction


## [0.1.1] - 2026-07-06

### Added

- Waste collection widget with automatic upcoming collection detection.
- Window widget supporting multiple configured entities.
- Typed widget configuration using dataclasses.

### Changed

- Refactored widget manager to use typed configuration objects.
- Simplified widget configuration handling.
- Improved project structure and maintainability.


## [0.2.0] - 2026-07-12

### Added

- Smart door widget combining lock and contact sensor (Zu / Auf / Offen / Warnung).
- Calendar widget for birthdays, appointments, holidays and vacation with
  Heute / Morgen / X-Tage formatting and configurable lookahead.
- Priority engine: every dashboard item carries `importance` and `visible`;
  the dashboard selects the five most important items on its own.
- Unit tests for Sprint 3 widgets and the priority engine (no Home Assistant
  installation required).

### Changed

- Window widget 2.0: shows room names ("○ Wohnen", "○ Wohnen+Essen")
  instead of a counter.
- Entity widget logs via `logging` instead of `print`.


## [0.3.0] - 2026-07-12

### Added

- Presence widget: shows who is home ("⌂ Jan+Anna"), an empty house
  ("⌂ Leer") is ranked more important than an occupied one.
- Fuel widget: tank level in percent or liters (configurable `unit`) plus
  refuel recommendation based on configurable level and price thresholds
  ("⛽ Tanken 1.65").
- Text helpers (`shorten`, `join_names`) for the narrow e-paper display.
- Appliance widget for washer/dryer: "🧺 WM Fertig" until manually reset
  via an input_boolean (resettable through the Weather Station's Matter
  buttons); "🧺 WM läuft" as background info. Example automations in
  docs/examples.md.

### Changed

- Renderer caps every widget value at 14 characters as a safety net;
  separator between widgets is a named constant (three spaces, used by
  the SwitchBot firmware as preferred line-break position).
- Window widget collapses three or more open rooms to "Wohnen+2".
- Calendar widget truncates long event names ("Max Muste…").


## [0.4.0] - 2026-07-12

### Added

- YAML widget configuration: widgets are configured in
  configuration.yaml under `switchbot_dashboard.widgets`, no code
  changes required. The Python config remains as fallback.
- Configuration validation with helpful error messages naming widget
  position, type and field, including suggestions for available options.
- Widget registry (`register_widget_type`) — custom widgets get
  configuration parsing and validation for free.
- Formatter registry (`FormatterFactory.register`) for custom formatters.
- `max_items` option to control how many widgets are displayed.
- Full widget reference in docs/configuration.md incl. custom widget
  and custom formatter guides.

### Changed

- All widgets are fully parameterized (door, weather and waste accept
  entity options); widget manager builds widgets generically from
  config dataclass fields.


## [0.5.0] - 2026-07-12

### Added

- Solar widget: PV production ("☀ 3.2kW"), hidden at night.
- Battery widget (generic): PV storage, e-bike or any battery;
  important when below threshold, optional always-on background info.
- EV widget: state of charge + charging status ("🔌 EV 64% lädt"),
  plug-in reminder when low and not charging.
- GitHub Actions CI: test matrix (Python 3.11–3.13), critical ruff
  checks, HACS validation.
- hacs.json and manifest metadata (version, issue tracker) for HACS.
- README installation guide (HACS + manual).


## [1.0.0] - 2026-07-12

First stable release. 🎉

A context-aware e-paper dashboard for the SwitchBot Weather Station:
instead of permanently showing every sensor, the priority engine picks
the five most relevant pieces of information for this moment.

- 12 widgets: weather, entity, door, window, waste, calendar, presence,
  fuel, appliance, solar, battery, ev
- Priority engine with situational importance per widget
- YAML configuration with validation and helpful error messages
- Public API for custom widgets and formatters
- 81 unit tests, CI, HACS-ready


## [1.1.0] - 2026-07-12

### Added

- Event-driven auto refresh: the dashboard watches all configured
  entities and updates the display on its own — with 5 s debounce,
  change detection (only send when the rendered line differs) and a
  60 s rate limit per SwitchBot recommendation. Periodic refresh every
  15 minutes catches date rollovers. Disable with `auto_refresh: false`.
- `refresh` service now forces an immediate update (bypasses the
  rate limit).
- Config flow: credentials (token, secret, device ID) can be set up
  via the UI incl. German and English translations; widgets stay
  in YAML.

### Changed

- Shared test helpers (`tests/helpers.py`) replace per-file stubs.
- Removed unused `BaseWidget.enabled()`/`NAME`; lint cleanup.


## [1.2.0] - 2026-07-12

### Added

- Local preview entity `sensor.switchbot_dashboard`: mirrors every
  rendered display line in Home Assistant (attributes:
  `sent_to_device`, `rendered_at`) — for development, dashboards and
  history without looking at the e-paper.
- `dry_run` option: render and publish the preview entity only, never
  call the SwitchBot API. Development mode without device and rate
  limit.