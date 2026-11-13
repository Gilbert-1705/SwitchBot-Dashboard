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
- API hardening based on official custom-page docs: outgoing payloads
  are capped at 300 bytes UTF-8 (without splitting characters), and
  SwitchBot status codes are evaluated and logged (190 = payload too
  long, 100 = OK).
- docs: official display constraints (byte limit, no line breaks,
  simple emojis, empty string clears the page, custom page must be
  selected on the device).


## [2.0.0] - 2026-07-12

Priority Engine 2.0. 🧠

### Added

- Official importance bands: 0-20 filler / 21-59 normal / 60+ always
  shown / 100 alarm (constants in const.py, documented semantics for
  widget authors).
- Quiet mode: filler items never push the display beyond
  `quiet_max_items` (default 3) - a calm day shows a calm display
  instead of five slots of background noise.
- Time-based importance (`ramp.time_based_importance`): information
  gets more urgent over time based on `state.last_changed`. The
  appliance done reminder ramps 30 → 60 (1 h) → 100 (3 h).
- German README (README.de.md).

### Changed

- All code comments and docstrings are English now; user-facing
  display strings stay German.
- Appliance done reminder starts as a side note (30) instead of a
  fixed 80 and grows louder the longer the laundry waits.


## [2.1.0] - 2026-07-12

Smart Alerts. ⚠️

### Added

- Alert widget: rules across multiple entities that Home Assistant
  never combines on its own — "window open + rain probability > 70%",
  "door open for 10 minutes + nobody home". Conditions: state,
  not_state, above, below, duration (AND-combined; OR via multiple
  alerts). Validated like every widget, with per-condition errors.
- Alarm mode: any item at importance 100 displaces normal items and
  fillers; only alarms and always-band items (>= 60) stay visible.

### Changed

- Appliance done ramp caps at 95 instead of 100: waiting laundry is
  loud but never triggers alarm mode.


## [2.2.0] - 2026-07-12

Groups & day context. 🕰

### Added

- Widget groups: widgets sharing a `group` render at most one item -
  the most important one. Door, window and an alert as group "haus"
  show one line instead of three.
- Day context via `boost`: per-widget time windows that raise or
  lower importance ("waste matters in the morning", "don't nag at
  night"). Windows may wrap over midnight, multiple windows add up,
  boosts are capped below alarm level.
- Both are base options on every widget (incl. custom widgets) and
  fully validated.


## [2.3.0] - 2026-11-13

### Added

- Appliance widget understands WashData-style status sensors:
  `starting`/`running`/`ending`, `paused`/`user_paused`,
  `delay_wait` ("wartet"), `interrupted`/`force_stopped` ("Abbruch",
  importance 65) and the done states `finished`/`clean`/
  `anti_wrinkle` - no manual done flag needed when the status entity
  reports "finished, not emptied" itself.
- `phase_entity`: shows the current phase while running
  ("🍽 GS Trocknen"); trailing temperatures ("Reinigen 45") are
  stripped.
- `remaining_entity`: remaining time, rounded up to 5-minute steps
  so the e-paper does not refresh every minute ("🍽 GS 45min").
- Dishwasher icon; docs: WashData example.

### Changed

- `done_entity` is optional now; the manual flag and a done state of
  the status entity work together.


## [2.3.1] - 2026-11-13

### Fixed

- HTTP 429 (SwitchBot rate limit) no longer raises: the API answers
  rate-limited requests without a JSON body, which crashed
  `send_text` with aiohttp's ContentTypeError. Non-200 answers and
  unreadable bodies are now mapped to a result with the HTTP status.
- A refused send is no longer treated as "display is up to date":
  the updater forgets the text, marks the preview entity as not sent
  and retries on its own after two minutes.
- A running or paused appliance sits in the normal importance band
  (30) instead of the filler band (15). Rendering against real
  sensor values showed that "GS Klarspülen" lost its slot to fillers
  such as "door closed" on a quiet day and never appeared.


## [2.3.2] - 2026-11-13

### Fixed

- The updater's state listener is a `@callback` now. Home Assistant
  runs plain listener functions in a worker thread, where scheduling
  the debounce timer is not allowed - auto refresh would have raised
  on every state change instead of updating the display. Found by
  reviewing the code against Home Assistant's threading rules before
  the first real deployment; the stubbed tests could not catch it.
- Without a YAML `widgets:` block the updater now watches the entities
  of the Python fallback configuration instead of none.


## [2.3.3] - 2026-11-13

### Fixed

Both found in the first minutes of real operation:

- The preview entity is only written when the text or its sent state
  changes. Any watched entity triggers a render every few seconds;
  writing `sensor.switchbot_dashboard` each time produced an identical
  recorder row per render (17 rows in 2.5 minutes).
- A pending debounce timer is no longer restarted by further state
  changes. A sensor reporting more often than the debounce time could
  have postponed the refresh indefinitely.


## [2.4.0] - 2026-11-13

### Added

- Fuel widget: dynamic price threshold. `max_price_entity` points at a
  reference sensor (e.g. a statistics helper with the lowest price of
  the last 7 days) and `price_margin` adds a surcharge - "good" then
  means "at most 3 cents above the recent low" instead of a fixed
  price that is outdated after a few weeks. The fixed `max_price`
  remains the fallback while the reference has no value.
