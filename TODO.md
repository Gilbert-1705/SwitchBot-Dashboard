# SwitchBot Dashboard — TODO

## Sprint 1 ✅ Foundation (v0.1.0)

- [x] Widget-System, Renderer, DashboardItem
- [x] Formatter-System, Prioritäten, Icons
- [x] Weather-, Entity-, Door-, Window-, Waste-Widget

## Sprint 2 ✅ Smart Home (v0.1.1)

- [x] Intelligentes Müllwidget
- [x] PowerFormatter, Fensterzählung, Türstatus, Wettertrend
- [x] Unicode/Icon-System

## Sprint 3 ✅ Smart Dashboard (v0.2.0)

- [x] Smart Door: Schloss + Türkontakt (Zu / Auf / Offen / Warnung)
- [x] Calendar Widget (Geburtstage, Termine, Feiertage, Urlaub)
- [x] Window 2.0: Raumnamen statt Zähler
- [x] Priority Engine: importance + visible, Dashboard wählt Top 5

## Sprint 4 ✅ Polish & Widget Library (v0.3.0)

- [x] Textkürzungen (shorten, join_names, Renderer-Cap 14 Zeichen)
- [x] Anwesenheits-Widget (⌂ Jan+Anna / ⌂ Leer)
- [x] Tank-Widget (Füllstand % oder l + Preisempfehlung)
- [x] Wäsche-Widget (WM/TR mit Fertig-Flag + manuellem Reset)
- [x] Window: Zustände Offen/Geschlossen/Gekippt, mode="state"
- [x] Appliance: run/pause/stop-Zustände

## Sprint 5 ✅ Konfiguration & Erweiterbarkeit (v0.4.0)

- [x] YAML-Konfiguration (configuration.yaml, Python-Config als Fallback)
- [x] Konfigurationsvalidierung mit verständlichen Fehlermeldungen
- [x] Widget-Registry (register_widget_type) für Custom Widgets
- [x] Formatter-Registry (FormatterFactory.register)
- [x] Widget-Dokumentation (docs/configuration.md)
- [x] max_items-Option

## Sprint 6 🚧 Open Source & v1.0

- [ ] GitHub Actions: Tests + Lint bei jedem Push
- [ ] hacs.json + manifest.json-Version pflegen (HACS-Aufnahme)
- [ ] Screenshots und GIFs vom echten Display (Jan)
- [ ] Icon-Kompatibilität am Gerät dokumentieren (welche Emojis rendert die Firmware?)
- [ ] Erstes GitHub-Release (Semver, Release Notes aus CHANGELOG)
- [ ] README: Installationsanleitung (HACS + manuell)

## Backlog / Technische Schulden

- [ ] refresh-Service implementieren: event-driven Refresh mit
      State-Listener, Debounce und Rate-Limit (max. 1 Call/min)
- [ ] Config Flow (UI-Setup statt YAML für token/secret/device_id)
- [ ] Gemeinsame Test-Helpers (FakeHass/FakeState) nach tests/helpers.py
- [ ] enabled() / visible nutzen oder entfernen
- [ ] Weitere Widgets: Batterie, Luftqualität, VPN/Serverstatus,
      Strompreis, PV, Wallbox
- [ ] Doppelte Leerzeilen nach Docstrings aufräumen (Lint)

## Vision v1.0

Ein Dashboard, das beim Vorbeigehen in Sekunden beantwortet:
Ist alles in Ordnung? Muss ich noch etwas tun? Gibt es heute etwas Wichtiges?
Kontextabhängige Priorisierung statt Sensor-Vollanzeige — Leitlinie
für alle weiteren Entscheidungen.
