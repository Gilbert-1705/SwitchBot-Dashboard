"""Display texts in several languages.

Everything the widgets print themselves ("Fertig", "Offen",
"Tanken", ...) comes from this table. Names the user configures
(room names, appliance labels, alert texts) and data-specific
mappings such as the waste types are not translated.

The language is a top-level option of the integration:

    switchbot_dashboard:
      language: en

Texts are kept short on purpose - the display wraps the line by
pixel width and every character counts.
"""

from .const import DOMAIN

DEFAULT_LANGUAGE = "de"
LANGUAGE_KEY = "language"

TEXTS = {
    "de": {
        "locked": "Zu",
        "unlocked": "Auf",
        "open": "Offen",
        "tilted": "Gekippt",
        "empty": "Leer",
        "refuel": "Tanken",
        "today": "Heute",
        "tomorrow": "Morgen",
        "days": "T",
        "done": "Fertig",
        "running": "läuft",
        "paused": "Pause",
        "waiting": "wartet",
        "aborted": "Abbruch",
        "minutes": "min",
        "charging": "lädt",
        "full": "Voll",
        "error": "Fehler",
    },
    "en": {
        "locked": "Locked",
        "unlocked": "Unlocked",
        "open": "Open",
        "tilted": "Tilted",
        "empty": "Empty",
        "refuel": "Refuel",
        "today": "Today",
        "tomorrow": "Tmrw",
        "days": "d",
        "done": "Done",
        "running": "running",
        "paused": "Paused",
        "waiting": "waiting",
        "aborted": "Aborted",
        "minutes": "min",
        "charging": "charging",
        "full": "Full",
        "error": "Error",
    },
}

LANGUAGES = tuple(sorted(TEXTS))


def translate(language: str, key: str) -> str:
    """Text for ``key``; falls back to the default language."""

    texts = TEXTS.get(language) or TEXTS[DEFAULT_LANGUAGE]

    return texts.get(key) or TEXTS[DEFAULT_LANGUAGE].get(key, key)


def language_of(hass) -> str:
    """Configured language of the integration (default: German)."""

    data = getattr(hass, "data", None)

    if isinstance(data, dict):
        return data.get(DOMAIN, {}).get(LANGUAGE_KEY) or DEFAULT_LANGUAGE

    return DEFAULT_LANGUAGE
