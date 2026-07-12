"""Tests für das Haushaltsgeräte-Widget (Waschmaschine/Trockner).

Ausführen (vom Repo-Root):

    python3 custom_components/switchbot_dashboard/tests/test_appliance.py
"""

import sys
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

if "homeassistant" not in sys.modules:
    ha = types.ModuleType("homeassistant")
    ha_core = types.ModuleType("homeassistant.core")
    ha_core.HomeAssistant = object
    ha_core.State = object
    ha_core.ServiceCall = object
    ha.core = ha_core
    sys.modules["homeassistant"] = ha
    sys.modules["homeassistant.core"] = ha_core

if "aiohttp" not in sys.modules:
    aiohttp = types.ModuleType("aiohttp")
    aiohttp.ClientSession = object
    sys.modules["aiohttp"] = aiohttp

from custom_components.switchbot_dashboard.icons import Icons
from custom_components.switchbot_dashboard.widgets.appliance import (
    ApplianceWidget,
)


class FakeState:

    def __init__(self, state):
        self.state = state
        self.attributes = {}


class FakeHass:

    def __init__(self, states):
        self.states = types.SimpleNamespace(get=states.get)


class ApplianceWidgetTest(unittest.TestCase):

    def _render(self, running, done):
        hass = FakeHass({
            "laeuft": FakeState(running),
            "fertig": FakeState(done),
        })
        return ApplianceWidget(
            hass,
            name="WM",
            running_entity="laeuft",
            done_entity="fertig",
            icon=Icons.LAUNDRY,
        ).render()

    def test_done_flag_shows_fertig(self):
        item = self._render("off", "on")
        self.assertEqual(item.value, "WM Fertig")
        self.assertEqual(item.icon, Icons.LAUNDRY)
        self.assertEqual(item.importance, 80)

    def test_running_is_background_info(self):
        item = self._render("on", "off")
        self.assertEqual(item.value, "WM läuft")
        self.assertEqual(item.importance, 15)

    def test_done_wins_over_running(self):
        # Trockner fertig, Waschmaschine läuft noch: Flag zählt
        item = self._render("on", "on")
        self.assertEqual(item.value, "WM Fertig")

    def test_idle_and_emptied_is_hidden(self):
        self.assertIsNone(self._render("off", "off"))

    def test_missing_entities_hidden(self):
        hass = FakeHass({})
        widget = ApplianceWidget(
            hass,
            name="WM",
            running_entity="laeuft",
            done_entity="fertig",
            icon=Icons.LAUNDRY,
        )
        self.assertIsNone(widget.render())


if __name__ == "__main__":
    unittest.main()
