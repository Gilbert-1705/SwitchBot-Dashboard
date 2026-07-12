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

## Sprint 6 🚧 Open Source & v1.0 (v0.5.0)

- [x] GitHub Actions: Tests + Lint + HACS-Validation bei jedem Push
- [x] hacs.json + manifest.json (Version, issue_tracker)
- [x] README: Installationsanleitung (HACS + manuell)
- [x] Energie-Widgets: solar, battery (generisch, auch eBike), ev
- [ ] Screenshots und GIFs vom echten Display (Jan)
- [ ] Icon-Kompatibilität am Gerät dokumentieren (welche Emojis rendert die Firmware?)
- [ ] Erstes GitHub-Release (Semver, Release Notes aus CHANGELOG)

## v1.1 ✅ Backlog-Abbau

- [x] Event-driven Refresh: State-Listener, 5s Debounce, 60s Rate-Limit,
      Änderungserkennung, periodischer Refresh (Datumswechsel)
- [x] refresh-Service erzwingt sofortiges Update
- [x] Config Flow (UI-Setup für token/secret/device_id, de/en)
- [x] Gemeinsame Test-Helpers (tests/helpers.py)
- [x] enabled()/NAME entfernt, Lint-Aufräumen

## v2.0 ✅ Priority Engine 2.0

- [x] Sprach-Cleanup: Code durchgehend Englisch, README.de.md
- [x] Importance-Bänder als offizielle Semantik:
      0-20 Füller / 21-59 normal / 60+ immer / 100 Alarm
- [x] Zeitrampe: Wichtigkeit steigt mit Dauer (state.last_changed),
      "WM Fertig": 30 → 60 (1h) → 100 (3h)
- [x] Ruhemodus: quiet_max_items (Standard 3), Füller verdrängen nichts

## v2.1 ✅ Smart Alerts

- [x] Alert-Widget für Zustandskombinationen
      (state/not_state/above/below, AND-verknüpft)
- [x] Zeitbedingungen (duration: Tür seit 10 min offen)
- [x] Alarmmodus: importance 100 verdrängt Normal- und Füller-Items

## v2.2 Gruppen & Tageskontext

- [ ] Widget-Gruppen: nur das wichtigste Item pro Gruppe
- [ ] Tageskontext: zeitabhängige Importance-Modifikatoren

## v3.x Plattform

- [ ] Plugin-System, Themes, Mehrsprachigkeit
- [ ] Weitere Displaygrößen / E-Paper-Displays
- [ ] Offizieller HACS-Store (brands-PR)

## Bewusst nicht geplant

Aktien, News, RSS, 7-Tage-Forecast, Server-Metriken als
Daueranzeige — kontextlose Daten verwässern das Konzept.

## Backlog

- [ ] Weitere Widgets nach Bedarf: Luftqualität, VPN/Serverstatus,
      Strompreis, Wallbox
- [ ] Options Flow (max_items/auto_refresh in der UI ändern)
- [ ] Refresh am Gerät testen (Debounce/Rate-Limit-Verhalten live)

## Vision v1.0

Ein Dashboard, das beim Vorbeigehen in Sekunden beantwortet:
Ist alles in Ordnung? Muss ich noch etwas tun? Gibt es heute etwas Wichtiges?
Kontextabhängige Priorisierung statt Sensor-Vollanzeige — Leitlinie
für alle weiteren Entscheidungen.
