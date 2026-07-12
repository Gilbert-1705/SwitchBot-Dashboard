"""Tests für die Energie-Widgets: solar, battery, ev.

Ausführen (vom Repo-Root):

    python3 custom_components/switchbot_dashboard/tests/test_energy.py
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

from custom_components.switchbot_dashboard.widgets.battery import (
    BatteryWidget,
)
from custom_components.switchbot_dashboard.widgets.ev import EvWidget
from custom_components.switchbot_dashboard.widgets.solar import SolarWidget


class FakeState:

    def __init__(self, state):
        self.state = state
        self.attributes = {}


class FakeHass:

    def __init__(self, states):
        self.states = types.SimpleNamespace(get=states.get)


class SolarWidgetTest(unittest.TestCase):

    def _render(self, power, min_power=50.0):
        hass = FakeHass({"pv": FakeState(power)})
        return SolarWidget(
            hass, entity="pv", min_power=min_power
        ).render()

    def test_producing_shows_formatted_power(self):
        item = self._render("3200")
        self.assertEqual(item.value, "3.2kW")
        self.assertEqual(item.importance, 15)

    def test_watt_range(self):
        self.assertEqual(self._render("450").value, "450W")

    def test_night_is_hidden(self):
        self.assertIsNone(self._render("0"))

    def test_below_min_power_hidden(self):
        self.assertIsNone(self._render("30"))

    def test_invalid_state_hidden(self):
        self.assertIsNone(self._render("unavailable"))


class BatteryWidgetTest(unittest.TestCase):

    def _render(self, level, name="eBike", show_always=False):
        hass = FakeHass({"akku": FakeState(level)})
        return BatteryWidget(
            hass,
            entity="akku",
            name=name,
            show_always=show_always,
        ).render()

    def test_low_battery_is_important(self):
        item = self._render("15")
        self.assertEqual(item.value, "eBike 15%")
        self.assertEqual(item.importance, 65)

    def test_ok_battery_hidden_by_default(self):
        self.assertIsNone(self._render("85"))

    def test_show_always_as_background(self):
        item = self._render("85", show_always=True)
        self.assertEqual(item.value, "eBike 85%")
        self.assertEqual(item.importance, 15)

    def test_without_name(self):
        item = self._render("15", name="")
        self.assertEqual(item.value, "15%")


class EvWidgetTest(unittest.TestCase):

    def _render(self, soc, charging="off", show_always=False):
        hass = FakeHass({
            "soc": FakeState(soc),
            "laden": FakeState(charging),
        })
        return EvWidget(
            hass,
            soc_entity="soc",
            charging_entity="laden",
            name="EV",
            show_always=show_always,
        ).render()

    def test_charging(self):
        item = self._render("64", charging="charging")
        self.assertEqual(item.value, "EV 64% lädt")
        self.assertEqual(item.importance, 30)

    def test_low_soc_not_charging_is_reminder(self):
        item = self._render("12")
        self.assertEqual(item.value, "EV 12%")
        self.assertEqual(item.importance, 65)

    def test_low_soc_but_charging_is_calm(self):
        item = self._render("12", charging="on")
        self.assertEqual(item.value, "EV 12% lädt")
        self.assertEqual(item.importance, 30)

    def test_ok_soc_hidden_by_default(self):
        self.assertIsNone(self._render("80"))

    def test_show_always(self):
        item = self._render("80", show_always=True)
        self.assertEqual(item.value, "EV 80%")
        self.assertEqual(item.importance, 15)

    def test_without_charging_entity(self):
        hass = FakeHass({"soc": FakeState("12")})
        item = EvWidget(hass, soc_entity="soc").render()
        self.assertEqual(item.value, "12%")


class YamlConfigTest(unittest.TestCase):

    def test_energy_widgets_via_yaml(self):
        from custom_components.switchbot_dashboard.config.schema import (
            build_widget_configs,
        )

        configs = build_widget_configs([
            {"type": "solar", "entity": "sensor.pv", "min_power": 100},
            {
                "type": "battery",
                "entity": "sensor.ebike",
                "name": "eBike",
                "show_always": True,
            },
            {
                "type": "ev",
                "soc_entity": "sensor.ev_soc",
                "charging_entity": "binary_sensor.ev_laden",
                "name": "EV",
            },
        ])

        self.assertEqual(len(configs), 3)
        self.assertEqual(configs[0].min_power, 100.0)
        self.assertTrue(configs[1].show_always)
        self.assertEqual(configs[2].charging_entity,
                         "binary_sensor.ev_laden")


if __name__ == "__main__":
    unittest.main()
