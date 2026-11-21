# SwitchBot Dashboard

*[English version](README.md)*

Eine Home-Assistant-Integration, die die SwitchBot Wetterstation in ein kontextbewusstes E-Ink-Dashboard verwandelt.

Anders als klassische Dashboards, die dauerhaft alle Sensoren anzeigen, zeigt das SwitchBot Dashboard nur die Informationen, die *jetzt gerade* relevant sind. Ein Blick im Vorbeigehen beantwortet in Sekunden:

> Ist alles in Ordnung? Muss ich noch etwas tun? Gibt es heute etwas Wichtiges?

```
🌡 21°C ☀   ○ Wohnen   🚪 Auf   🗑 Rest Heute   🎂 Oma
```

Und an einem ruhigen Tag:

```
🌡 21°C ☀   ●   🚪 Zu
```

## Status

✅ Stabil (v2.7.0) — siehe [CHANGELOG](CHANGELOG.md)

## Funktionsweise

Jedes Widget meldet bei jedem Rendern zwei Werte:

- **priority** — an welcher Stelle der Zeile es steht (Reihenfolge)
- **importance** — wie relevant die Information *in diesem Moment* ist

Die Priority Engine sammelt alle sichtbaren Einträge, behält die fünf wichtigsten und zeigt sie in der konfigurierten Reihenfolge. Eine abgeschlossene, aber offene Tür (importance 100) schlägt immer den Stromverbrauch (importance 10).

## Widgets

| Widget | Beispiel | Zeigt |
|---|---|---|
| Weather | `🌡 21°C ☀` | Temperatur + Trend; ruhig gegen Zappeln, optional Referenzsensor gegen Sonne auf dem Sensor |
| Entity | `P 380W` | Beliebige Entität mit Formatter (Leistung, Zahl, …) |
| Door | `🚪 Zu` / `! Offen` | Smart Lock + Türkontakt kombiniert: Zu, Auf, Offen, Warnung |
| Window | `○ Wohnen+Essen` / `○ Gekippt` | Offene Räume mit Namen (`mode="rooms"`) oder nur der Zustand (`mode="state"`), `●` wenn alles zu ist |
| Waste | `🗑 Rest Morgen` | Nächste Müllabfuhr in den kommenden 3 Tagen |
| Calendar | `🎂 Oma`, `📅 Zahnarzt 2T` | Geburtstage, Termine, Feiertage, Urlaub |
| Presence | `⌂ Jan+Anna` / `⌂ Leer` | Wer zu Hause ist; ein leeres Haus wird wichtiger |
| Fuel | `⛽ Tanken 1.65` | Tankfüllstand (% oder Liter) + Tankempfehlung nach Füllstand und Preis |
| Appliance | `🧺 WM Fertig` / `🍽 GS Trocknen` | Waschmaschine, Trockner, Geschirrspüler: Phase oder Restzeit während des Laufs, Fertig-Erinnerung, die mit der Zeit lauter wird; mit einfachen Sensoren und WashData (siehe [Beispiele](docs/examples.md)) |
| Solar | `☀ 3.2kW` | PV-Erzeugung, nachts ausgeblendet |
| Battery | `🔋 eBike 15%` | Beliebiger Akku (PV-Speicher, E-Bike, …), wichtig wenn leer |
| EV | `🔌 64% lädt` | Ladestand und Ladestatus des E-Autos, Erinnerung wenn leer und nicht eingesteckt |
| Alert | `! Regen rein` | Smart Alerts: Regeln über mehrere Entitäten („Fenster offen + Regen > 70 %“), lösen den Alarmmodus aus |
| Threshold | `☁ CO₂ 1450` | Beliebiger Zahlensensor, nur sichtbar außerhalb der Grenzen (Luftqualität, Strompreis, Luftfeuchte) |
| Status | `! NAS+VPN` | Zeigt nur, was ausgefallen ist: Server, VPN, Dienste |
| Wallbox | `🔌 WB 7.4kW` | Ladepunkt: Leistung beim Laden, fertig, Fehler |
| Media | `♪ Bohemian Rhapsody` | Aktueller Titel eines Media Players, nur während der Wiedergabe |

## Installation

**HACS (empfohlen):** HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories → `https://github.com/Gilbert-1705/SwitchBot-Dashboard` als *Integration* hinzufügen, installieren, Home Assistant neu starten.

**Manuell:** Den Ordner `custom_components/switchbot_dashboard` nach `config/custom_components/` kopieren und neu starten.

## Konfiguration

Die Zugangsdaten (Token, Secret und Geräte-ID aus den Entwickleroptionen der SwitchBot-App) kommen per YAML oder per UI (Einstellungen → Geräte & Dienste); die Widgets werden in der `configuration.yaml` konfiguriert:

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

Die vollständige Widget-Referenz mit allen Optionen steht in [docs/configuration.md](docs/configuration.md), fertige Beispiele (Wäsche-Erinnerung, Geschirrspüler mit WashData, virtuelle Tasten) in [docs/examples.md](docs/examples.md) — beides auf Englisch. Eigene Widgets und Formatter lassen sich über die [Widget-API](docs/configuration.md#custom-widgets) registrieren.

Services: `switchbot_dashboard.refresh` rendert und sendet sofort, `switchbot_dashboard.preview` rendert und sendet das Dashboard, `switchbot_dashboard.reload` übernimmt einen geänderten YAML-Block ohne Neustart, `switchbot_dashboard.send_text` sendet beliebigen Text.

## Hinweise zum Display

Das Display zeichnet nicht neu, sobald ein neuer Text ankommt: Es holt die Custom-Seite nach eigenem Zeitplan ab (zu den festen Uhrzeiten aus der SwitchBot-App, sonst etwa alle drei Stunden). Kurze Ereignisse — ein zehn Minuten gekipptes Fenster — erreichen den Bildschirm unter Umständen nie; das Dashboard ist für den Stand gemacht, den man im Vorbeigehen sieht.

Die Firmware bricht die Zeile selbst um (pixelbasiert, bevorzugt an Leerzeichen). Der Renderer trennt die Widgets deshalb mit drei Leerzeichen und kürzt jeden Widget-Text auf 14 Zeichen (das Media-Widget bekommt 20); die Widgets kürzen zusätzlich selbst (`Wohnen+2`, `Max Muste…`).

## Entwicklung

`sensor.switchbot_dashboard` spiegelt die gerenderte Zeile in Home Assistant (Attribute `sent_to_device`, `rendered_at`). Mit `dry_run: true` wird die SwitchBot-API nie aufgerufen — Widget-Entwicklung ohne Gerät und ohne Rate-Limit. Die Architektur ist in [docs/architecture.md](docs/architecture.md) beschrieben.

## Tests

```
for t in custom_components/switchbot_dashboard/tests/test_*.py; do python3 "$t"; done
```

Jede Testdatei läuft auch einzeln. Die Tests ersetzen Home Assistant durch Stubs und brauchen keine HA-Installation.

## Roadmap

Erledigtes und Offenes: [TODO.md](TODO.md). Als Nächstes: Screenshots vom echten Display, eine Liste der Emojis, die die Firmware darstellt, das erste GitHub-Release und die Aufnahme in den offiziellen HACS-Store.

## Lizenz

MIT — siehe [LICENSE](LICENSE). Der Code darf genutzt, verändert und weitergegeben werden, auch kommerziell, solange der Copyright-Hinweis und der Lizenztext erhalten bleiben. Die Software wird ohne jede Gewährleistung bereitgestellt.

SwitchBot ist eine Marke des jeweiligen Inhabers. Dieses Projekt ist eine unabhängige Community-Integration und steht in keiner Verbindung zu SwitchBot oder Home Assistant und wird von diesen nicht unterstützt.
