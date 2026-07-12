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
- Fuel widget: tank level in liters plus refuel recommendation based on
  configurable level and price thresholds ("⛽ Tanken 1.65").
- Text helpers (`shorten`, `join_names`) for the narrow e-paper display.

### Changed

- Renderer caps every widget value at 14 characters as a safety net;
  separator between widgets is a named constant (three spaces, used by
  the SwitchBot firmware as preferred line-break position).
- Window widget collapses three or more open rooms to "Wohnen+2".
- Calendar widget truncates long event names ("Max Muste…").