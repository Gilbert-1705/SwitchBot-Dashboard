# SwitchBot Dashboard — TODO

## Sprint 1 ✅ Foundation (v0.1.0)

- [x] Widget system, renderer, DashboardItem
- [x] Formatter system, priorities, icons
- [x] Weather, entity, door, window and waste widgets

## Sprint 2 ✅ Smart Home (v0.1.1)

- [x] Smart waste widget
- [x] PowerFormatter, window count, door state, weather trend
- [x] Unicode/icon system

## Sprint 3 ✅ Smart Dashboard (v0.2.0)

- [x] Smart door: lock + door contact (Zu / Auf / Offen / warning)
- [x] Calendar widget (birthdays, appointments, holidays, vacation)
- [x] Window 2.0: room names instead of a counter
- [x] Priority engine: importance + visible, the dashboard picks the top 5

## Sprint 4 ✅ Polish & Widget Library (v0.3.0)

- [x] Text shortening (shorten, join_names, renderer cap of 14 characters)
- [x] Presence widget (⌂ Jan+Anna / ⌂ Leer)
- [x] Fuel widget (level in % or l + refuel recommendation)
- [x] Laundry widget (washer/dryer with done flag + manual reset)
- [x] Window: states Offen/Geschlossen/Gekippt, mode="state"
- [x] Appliance: run/pause/stop states

## Sprint 5 ✅ Configuration & Extensibility (v0.4.0)

- [x] YAML configuration (configuration.yaml, Python config as fallback)
- [x] Configuration validation with clear error messages
- [x] Widget registry (register_widget_type) for custom widgets
- [x] Formatter registry (FormatterFactory.register)
- [x] Widget documentation (docs/configuration.md)
- [x] max_items option

## Sprint 6 ✅ Open Source & v1.0 (v0.5.0)

- [x] GitHub Actions: tests + lint + HACS validation on every push
- [x] hacs.json + manifest.json (version, issue_tracker)
- [x] README: installation guide (HACS + manual)
- [x] Energy widgets: solar, battery (generic, also e-bike), ev
- Open items moved to "Backlog"

## v1.1 ✅ Backlog Cleanup

- [x] Event-driven refresh: state listener, 5 s debounce, 60 s rate limit,
      change detection, periodic refresh (day change)
- [x] refresh service forces an immediate update
- [x] Config flow (UI setup for token/secret/device_id, de/en)
- [x] Shared test helpers (tests/helpers.py)
- [x] enabled()/NAME removed, lint cleanup

## v2.0 ✅ Priority Engine 2.0

- [x] Language cleanup: code in English throughout, README.de.md
- [x] Importance bands as official semantics:
      0-20 filler / 21-59 normal / 60+ always / 100 alarm
- [x] Time ramp: importance grows with duration (state.last_changed),
      "WM Fertig": 30 → 60 (1 h) → 95 (3 h)
- [x] Quiet mode: quiet_max_items (default 3), fillers displace nothing

## v2.1 ✅ Smart Alerts

- [x] Alert widget for combinations of states
      (state/not_state/above/below, combined with AND)
- [x] Time conditions (duration: door open for 10 min)
- [x] Alarm mode: importance 100 displaces normal and filler items

## v2.2 ✅ Groups & Day Context

- [x] Widget groups: group option, only the most important item per group
- [x] Day context: boost option (time window + add, also negative,
      across midnight, capped below alarm level)

## v2.3 ✅ WashData

- [x] Appliance widget understands WashData states (clean, delay_wait,
      interrupted, ...), done_entity optional
- [x] Phase (phase_entity) and remaining time (remaining_entity, 5-minute steps)

## v2.4 ✅ Dynamic Fuel Recommendation

- [x] max_price_entity + price_margin (e.g. 7-day low + 3 ct)

## v2.5 ✅ Operations & Platform

- [x] Restart-proof reminders and alert durations (own timestamps)
- [x] Power display rounded to 10 W
- [x] reload service: apply the configuration without a restart
- [x] Options flow (max_items, quiet_max_items, auto_refresh, dry_run,
      language)
- [x] Display texts in several languages (de/en)
- [x] Widgets: threshold (air quality, electricity price), status
      (server/VPN), wallbox

## v2.6 ✅ Music

- [x] Media widget: current title, only while playing
- [x] Text length per item (max_length)

## v2.7 ✅ Calmer Display

- [x] Temperature with hysteresis (no flipping around x.5 degrees)
- [x] Reference sensor as fallback when the local sensor is in the sun
- [x] Spaces inside an item as no-break spaces (no wrap inside an item)

## v2.8 / v2.9 ✅ Display Simulator & Fit to Display

- [x] Display simulator: predicts line breaks and space, calibrated on
      reference photos (attributes display_lines/display_fits/display_scale,
      CLI with a mock picture)
- [x] Line test: with six lines the display halves the font (no cut-off)
- [x] Fit to display (fit_display): leave out the least important items
      instead of shrinking the font

## v2.10 ✅ Configuration in the UI

- [x] Widget editor: every widget as a config subentry
      ("Add widget", edit, delete), forms generated from the widget
      definitions, labels de/en
- [x] One-time import of the YAML block (credentials, options, widgets),
      repair notice for the leftover block

## v3.x Platform

- [ ] Plugin system, themes
- [ ] More display sizes / e-paper displays
- [ ] Official HACS store (brands PR)
- [ ] Display buttons of the Weather Station (no way into Home Assistant
      known yet; virtual buttons set up as a stand-in)

## Deliberately not planned

Stocks, news, RSS, 7-day forecast, server metrics as a permanent
display — data without context dilutes the concept.

## Backlog

- [ ] Screenshots and GIFs of the real display for the README
- [ ] List of the emojis the firmware renders (confirmed: 🌡 ☀ 🧺 🍽 🚪 ⛽ 🗑 📅 ○ ⌂ ♪;
      not rendered: 🔋; open: ● ☂ ☁ 🔌 🎂 ★ ✈)
- [ ] Simulator: exact limit (4 or 5 lines) and sizes between full and half
- [ ] Battery widget: another default icon, 🔋 is not rendered
- [ ] Battery warning for the Weather Station itself (Bluetooth sensor)
- [ ] Widget editor: friendly names in the widget titles instead of entity IDs
- [x] First GitHub release (semver, release notes from the CHANGELOG)
- [ ] More languages

## Vision

A dashboard that answers in seconds when walking past:
Is everything fine? Do I still have to do something? Is anything important today?
Context-aware prioritization instead of showing every sensor — the guiding
principle for all further decisions.
