"""Tests for the display texts in several languages.

Run (from the repo root):

    python3 custom_components/switchbot_dashboard/tests/test_i18n.py
"""

import unittest
from datetime import date, timedelta

import helpers  # noqa: F401  (stubs HA/aiohttp, sets sys.path)
from helpers import FakeHass, FakeState

from custom_components.switchbot_dashboard.const import DOMAIN
from custom_components.switchbot_dashboard.i18n import (
    DEFAULT_LANGUAGE,
    LANGUAGES,
    TEXTS,
    language_of,
    translate,
)
from custom_components.switchbot_dashboard.widgets.appliance import (
    ApplianceWidget,
)
from custom_components.switchbot_dashboard.widgets.calendar import (
    CalendarWidget,
)
from custom_components.switchbot_dashboard.widgets.door import DoorWidget
from custom_components.switchbot_dashboard.widgets.ev import EvWidget
from custom_components.switchbot_dashboard.widgets.fuel import FuelWidget
from custom_components.switchbot_dashboard.widgets.presence import (
    PresenceWidget,
)
from custom_components.switchbot_dashboard.widgets.waste import WasteWidget
from custom_components.switchbot_dashboard.widgets.window import WindowWidget


def hass_in(language, states):
    hass = FakeHass(states)
    if language is not None:
        hass.data[DOMAIN] = {"language": language}
    return hass


class TranslationTableTest(unittest.TestCase):

    def test_every_language_has_every_key(self):
        reference = set(TEXTS[DEFAULT_LANGUAGE])
        for language in LANGUAGES:
            self.assertEqual(set(TEXTS[language]), reference, language)

    def test_no_empty_texts(self):
        for language, texts in TEXTS.items():
            for key, text in texts.items():
                self.assertTrue(text, f"{language}.{key}")

    def test_unknown_language_falls_back_to_default(self):
        self.assertEqual(translate("xx", "done"), "Fertig")

    def test_unknown_key_returns_the_key(self):
        self.assertEqual(translate("de", "gibtsnicht"), "gibtsnicht")

    def test_default_language_without_configuration(self):
        self.assertEqual(language_of(FakeHass({})), "de")
        self.assertEqual(language_of(None), "de")

    def test_configured_language(self):
        self.assertEqual(language_of(hass_in("en", {})), "en")


class EnglishOutputTest(unittest.TestCase):

    def test_door(self):
        def door(lock, contact):
            hass = hass_in("en", {
                "lock": FakeState(lock),
                "contact": FakeState(contact),
            })
            return DoorWidget(
                hass, lock_entity="lock", contact_entity="contact"
            ).render().value

        self.assertEqual(door("locked", "off"), "Locked")
        self.assertEqual(door("unlocked", "off"), "Unlocked")
        self.assertEqual(door("unlocked", "on"), "Open")

    def test_window_state_mode(self):
        def window(a, b):
            hass = hass_in("en", {"a": FakeState(a), "b": FakeState(b)})
            return WindowWidget(
                hass, entities={"a": "A", "b": "B"}, mode="state"
            ).render().value

        self.assertEqual(window("Offen", "Geschlossen"), "Open")
        self.assertEqual(window("Gekippt", "Geschlossen"), "Tilted")
        self.assertEqual(window("Offen", "Gekippt"), "Open+Tilted")

    def test_presence(self):
        hass = hass_in("en", {"p": FakeState("not_home")})
        item = PresenceWidget(hass, entities={"p": "Jan"}).render()
        self.assertEqual(item.value, "Empty")

    def test_fuel(self):
        hass = hass_in("en", {
            "tank": FakeState("12"),
            "preis": FakeState("1.65"),
        })
        item = FuelWidget(
            hass, level_entity="tank", price_entity="preis"
        ).render()
        self.assertEqual(item.value, "Refuel 1.65")

    def test_waste(self):
        def waste(days):
            when = (date.today() + timedelta(days=days)).isoformat()
            hass = hass_in("en", {
                "muell": FakeState("x", {when: "Restabfall"}),
            })
            return WasteWidget(hass, entity="muell").render().value

        self.assertEqual(waste(0), "Rest Today")
        self.assertEqual(waste(1), "Rest Tmrw")
        self.assertEqual(waste(3), "Rest 3d")

    def test_calendar(self):
        when = (date.today() + timedelta(days=2)).isoformat()
        hass = hass_in("en", {
            "cal": FakeState("off", {
                "message": "Dentist", "start_time": when,
            }),
        })
        item = CalendarWidget(hass, entity="cal", icon="x").render()
        self.assertEqual(item.value, "Dentist 2d")

    def test_appliance(self):
        def appliance(state, **extra):
            states = {"s": FakeState(state)}
            states.update(extra)
            hass = hass_in("en", states)
            return ApplianceWidget(
                hass, name="DW", running_entity="s",
                remaining_entity="rest",
            ).render().value

        self.assertEqual(appliance("running"), "DW running")
        self.assertEqual(appliance("paused"), "DW Paused")
        self.assertEqual(appliance("delay_wait"), "DW waiting")
        self.assertEqual(appliance("interrupted"), "DW Aborted")
        self.assertEqual(appliance("clean"), "DW Done")
        self.assertEqual(
            appliance("running", rest=FakeState("42")), "DW 45min"
        )

    def test_ev(self):
        hass = hass_in("en", {
            "soc": FakeState("64"),
            "laden": FakeState("charging"),
        })
        item = EvWidget(
            hass, soc_entity="soc", charging_entity="laden"
        ).render()
        self.assertEqual(item.value, "64% charging")


class GermanStaysDefaultTest(unittest.TestCase):
    """Without a language option nothing changes for existing setups."""

    def test_default_output_is_german(self):
        hass = FakeHass({"s": FakeState("clean")})
        item = ApplianceWidget(
            hass, name="GS", running_entity="s"
        ).render()
        self.assertEqual(item.value, "GS Fertig")

    def test_explicit_german(self):
        hass = hass_in("de", {
            "lock": FakeState("locked"),
            "contact": FakeState("off"),
        })
        item = DoorWidget(
            hass, lock_entity="lock", contact_entity="contact"
        ).render()
        self.assertEqual(item.value, "Zu")


if __name__ == "__main__":
    unittest.main()
