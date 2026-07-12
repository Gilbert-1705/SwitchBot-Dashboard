# SwitchBot Dashboard

*[English version](README.md)*

Eine Home-Assistant-Integration, die die SwitchBot Wetterstation in ein kontextbewusstes E-Ink-Dashboard verwandelt.

Anders als klassische Dashboards, die dauerhaft alle Sensoren anzeigen, zeigt das SwitchBot Dashboard nur die Informationen, die *jetzt gerade* relevant sind. Ein Blick im Vorbeigehen beantwortet in Sekunden:

> Ist alles in Ordnung? Muss ich noch etwas tun? Gibt es heute etwas Wichtiges?

```
🌡 21°C ☀   ○ Offen   🗑 Rest Heute   🎂 Oma   🧺 WM Fertig
```

Und an einem ruhigen Tag:

```
🌡 21°C ☀   ●   🚪 Zu
```

## Funktionsweise

Jedes Widget meldet bei jedem Rendern zwei Werte: `priority` (Anzeigereihenfolge) und `importance` (wie relevant ist die Information *in diesem Moment*). Die Priority Engine wählt aus allen sichtbaren Items die wichtigsten aus — eine abgeschlossene, aber offene Tür (importance 100) schlägt immer den Stromverbrauch (10).

## Installation

**HACS (empfohlen):** HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories → `https://github.com/Gilbert-1705/SwitchBot-Dashboard` als *Integration* hinzufügen, installieren, Home Assistant neu starten.

**Manuell:** Den Ordner `custom_components/switchbot_dashboard` nach `config/custom_components/` kopieren und neu starten.

## Konfiguration

Die Zugangsdaten (Token, Secret, Geräte-ID aus den Entwickleroptionen der SwitchBot-App) kommen per UI (Einstellungen → Geräte & Dienste) oder YAML; die Widgets werden per YAML konfiguriert:

```yaml
switchbot_dashboard:
  token: !secret switchbot_token
  secret: !secret switchbot_secret
  device_id: !secret switchbot_device_id
  widgets:
    - type: weather
    - type: waste
      entity: sensor.muellkalender
    - type: calendar
      entity: calendar.geburtstage
      icon: "🎂"
      days: 1
```

Die vollständige Widget-Referenz (12 Widgets, alle Optionen), Anleitungen für eigene Widgets und Formatter sowie die Display-Eigenheiten stehen in [docs/configuration.md](docs/configuration.md) (Englisch). Beispiel-Automationen (z.B. Waschmaschinen-Reminder mit Reset über die Display-Buttons) in [docs/examples.md](docs/examples.md).

## Entwicklung

`sensor.switchbot_dashboard` spiegelt die gerenderte Displayzeile lokal in Home Assistant; mit `dry_run: true` wird die SwitchBot-API nie aufgerufen — Widget-Entwicklung ohne Gerät und Rate-Limit. Tests laufen ohne HA-Installation:

```
python3 custom_components/switchbot_dashboard/tests/test_sprint3.py
```

## Lizenz

MIT — siehe [LICENSE](LICENSE).
