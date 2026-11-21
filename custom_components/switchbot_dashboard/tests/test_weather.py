"""Tests for the weather widget: hysteresis and reference sensor.

Run (from the repo root):

    python3 custom_components/switchbot_dashboard/tests/test_weather.py
"""

import unittest

import helpers  # noqa: F401  (stubs HA/aiohttp, sets sys.path)
from helpers import FakeHass, FakeState

from custom_components.switchbot_dashboard.config.schema import (
    build_widget_configs,
)
from custom_components.switchbot_dashboard.render import render_dashboard
from custom_components.switchbot_dashboard.updater import collect_entities
from custom_components.switchbot_dashboard.widgets.weather import (
    WeatherWidget,
)


class HysteresisTest(unittest.TestCase):

    def setUp(self):
        # FakeHass reads from this dict, so it can be changed in place
        self.states = {"temp": FakeState("3.4")}
        self.hass = FakeHass(self.states)

    def _show(self, value, **kwargs):
        self.states["temp"] = FakeState(value)
        widget = WeatherWidget(
            self.hass, temperature_entity="temp", trend_entity="", **kwargs
        )
        return widget.render().value

    def test_first_value_is_rounded(self):
        self.assertEqual(self._show("3.4"), "3°C")

    def test_jitter_around_the_border_is_ignored(self):
        self.assertEqual(self._show("3.4"), "3°C")
        # 3.6 would round to 4, but is only 0.6 away from the shown 3
        self.assertEqual(self._show("3.6"), "3°C")
        self.assertEqual(self._show("3.5"), "3°C")
        self.assertEqual(self._show("3.7"), "3°C")

    def test_a_real_change_comes_through(self):
        self.assertEqual(self._show("3.4"), "3°C")
        self.assertEqual(self._show("3.8"), "4°C")
        # and back down only once clearly below
        self.assertEqual(self._show("3.4"), "4°C")
        self.assertEqual(self._show("3.2"), "3°C")

    def test_big_jumps_are_shown_at_once(self):
        self.assertEqual(self._show("3.4"), "3°C")
        self.assertEqual(self._show("9.1"), "9°C")

    def test_hysteresis_can_be_switched_off(self):
        self.assertEqual(self._show("3.4", hysteresis=0), "3°C")
        self.assertEqual(self._show("3.6", hysteresis=0), "4°C")


class ReferenceSensorTest(unittest.TestCase):

    def _render(self, local, reference, **kwargs):
        states = {"temp": FakeState(local)}
        if reference is not None:
            states["dwd"] = FakeState(reference)
        widget = WeatherWidget(
            FakeHass(states), temperature_entity="temp", trend_entity="",
            reference_entity="dwd", **kwargs
        )
        item = widget.render()
        return None if item is None else item.value

    def test_local_value_while_plausible(self):
        self.assertEqual(self._render("5.2", "2.1"), "5°C")

    def test_sun_on_the_sensor_falls_back_to_the_reference(self):
        # the Eve sensor in the sun: 32 °C on a 9 °C day
        self.assertEqual(self._render("32.0", "9.0"), "9°C")

    def test_deviation_is_configurable(self):
        self.assertEqual(self._render("5.2", "2.1", max_deviation=2), "2°C")

    def test_unavailable_local_sensor_uses_the_reference(self):
        self.assertEqual(self._render("unavailable", "2.1"), "2°C")

    def test_unavailable_reference_keeps_the_local_value(self):
        self.assertEqual(self._render("32.0", "unavailable"), "32°C")

    def test_both_unavailable_hides_the_widget(self):
        self.assertIsNone(self._render("unavailable", "unknown"))

    def test_without_reference_nothing_changes(self):
        widget = WeatherWidget(
            FakeHass({"temp": FakeState("32.0")}),
            temperature_entity="temp", trend_entity="",
        )
        self.assertEqual(widget.render().value, "32°C")


class FallbackHysteresisTest(unittest.TestCase):
    """At the deviation limit the source must not flip back and forth."""

    def setUp(self):
        self.states = {"dwd": FakeState("1.3")}
        self.hass = FakeHass(self.states)

    def _show(self, local):
        self.states["temp"] = FakeState(local)
        widget = WeatherWidget(
            self.hass, temperature_entity="temp", trend_entity="",
            reference_entity="dwd", hysteresis=0,
        )
        return widget.render().value

    def test_stays_on_the_reference_near_the_limit(self):
        self.assertEqual(self._show("5.0"), "5°C")   # 3.7 off: local
        self.assertEqual(self._show("5.6"), "1°C")   # 4.3 off: reference
        self.assertEqual(self._show("5.2"), "1°C")   # 3.9 off: still reference
        self.assertEqual(self._show("4.6"), "1°C")   # 3.3 off: still reference
        self.assertEqual(self._show("4.2"), "4°C")   # 2.9 off: local again


class WeatherYamlTest(unittest.TestCase):

    def test_options_via_yaml_and_reference_is_watched(self):
        configs = build_widget_configs([{
            "type": "weather",
            "temperature_entity": "sensor.eve",
            "trend_entity": "sensor.trend",
            "reference_entity": "sensor.dwd",
            "max_deviation": 3,
            "hysteresis": 1,
        }])
        self.assertIn("sensor.dwd", collect_entities(configs))

        hass = FakeHass({
            "sensor.eve": FakeState("30.4"),
            "sensor.dwd": FakeState("8.6"),
            "sensor.trend": FakeState("sunny"),
        })
        self.assertEqual(render_dashboard(hass, configs), "🌡 9°C ☀")


if __name__ == "__main__":
    unittest.main()
