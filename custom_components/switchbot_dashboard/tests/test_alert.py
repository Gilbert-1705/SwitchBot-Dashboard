"""Tests for smart alerts and alarm mode.

Run (from the repo root):

    python3 custom_components/switchbot_dashboard/tests/test_alert.py
"""

import unittest
from datetime import datetime, timedelta, timezone

import helpers  # noqa: F401  (stubs HA/aiohttp, sets sys.path)
from helpers import FakeHass, FakeState

from custom_components.switchbot_dashboard.config.schema import (
    ConfigError,
    build_widget_configs,
)
from custom_components.switchbot_dashboard.dashboard import (
    DashboardRenderer,
)
from custom_components.switchbot_dashboard.dashboard.item import (
    DashboardItem,
)
from custom_components.switchbot_dashboard.widgets.alert import AlertWidget


def make_alert(hass, conditions, **kwargs):
    return AlertWidget(
        hass, name="Achtung", conditions=conditions, **kwargs
    )


class AlertConditionsTest(unittest.TestCase):

    def test_all_conditions_met_fires(self):
        hass = FakeHass({
            "fenster": FakeState("Offen"),
            "regen": FakeState("85"),
        })
        item = make_alert(hass, [
            {"entity": "fenster", "state": "Offen"},
            {"entity": "regen", "above": 70},
        ]).render()

        self.assertEqual(item.value, "Achtung")
        self.assertEqual(item.importance, 100)

    def test_one_condition_failing_hides(self):
        hass = FakeHass({
            "fenster": FakeState("Geschlossen"),
            "regen": FakeState("85"),
        })
        item = make_alert(hass, [
            {"entity": "fenster", "state": "Offen"},
            {"entity": "regen", "above": 70},
        ]).render()

        self.assertIsNone(item)

    def test_state_match_is_case_insensitive(self):
        hass = FakeHass({"tuer": FakeState("OFFEN")})
        item = make_alert(hass, [
            {"entity": "tuer", "state": "offen"},
        ]).render()
        self.assertIsNotNone(item)

    def test_state_accepts_list(self):
        hass = FakeHass({"tuer": FakeState("Gekippt")})
        item = make_alert(hass, [
            {"entity": "tuer", "state": ["Offen", "Gekippt"]},
        ]).render()
        self.assertIsNotNone(item)

    def test_not_state(self):
        # door open + nobody home
        hass = FakeHass({
            "tuer": FakeState("on"),
            "jan": FakeState("not_home"),
        })
        item = make_alert(hass, [
            {"entity": "tuer", "state": "on"},
            {"entity": "jan", "not_state": "home"},
        ]).render()
        self.assertIsNotNone(item)

    def test_below(self):
        hass = FakeHass({"temp": FakeState("2.5")})
        item = make_alert(hass, [
            {"entity": "temp", "below": 3},
        ]).render()
        self.assertIsNotNone(item)

    def test_duration_not_reached(self):
        recent = datetime.now(timezone.utc) - timedelta(minutes=2)
        hass = FakeHass({
            "tuer": FakeState("on", last_changed=recent),
        })
        item = make_alert(hass, [
            {"entity": "tuer", "state": "on", "duration": 600},
        ]).render()
        self.assertIsNone(item)

    def test_duration_reached(self):
        old = datetime.now(timezone.utc) - timedelta(minutes=15)
        hass = FakeHass({
            "tuer": FakeState("on", last_changed=old),
        })
        item = make_alert(hass, [
            {"entity": "tuer", "state": "on", "duration": 600},
        ]).render()
        self.assertIsNotNone(item)

    def test_missing_entity_never_fires(self):
        hass = FakeHass({})
        item = make_alert(hass, [
            {"entity": "gibtsnicht", "state": "on"},
        ]).render()
        self.assertIsNone(item)

    def test_unavailable_never_fires(self):
        hass = FakeHass({"regen": FakeState("unavailable")})
        item = make_alert(hass, [
            {"entity": "regen", "above": 70},
        ]).render()
        self.assertIsNone(item)

    def test_non_numeric_above_never_fires(self):
        hass = FakeHass({"regen": FakeState("viel")})
        item = make_alert(hass, [
            {"entity": "regen", "above": 70},
        ]).render()
        self.assertIsNone(item)

    def test_custom_importance(self):
        hass = FakeHass({"x": FakeState("on")})
        item = make_alert(
            hass,
            [{"entity": "x", "state": "on"}],
            importance=70,
        ).render()
        self.assertEqual(item.importance, 70)


class AlarmModeTest(unittest.TestCase):

    def test_alarm_displaces_normal_and_filler(self):
        r = DashboardRenderer(max_items=5)
        r.add(DashboardItem("!", "Regen rein", priority=50,
                            importance=100))
        r.add(DashboardItem("W", "21°C", priority=100, importance=90))
        r.add(DashboardItem("N", "Termin 2T", priority=500,
                            importance=45))
        r.add(DashboardItem("P", "280W", priority=200, importance=10))

        values = [i.value for i in r.select()]

        self.assertIn("Regen rein", values)
        self.assertIn("21°C", values)       # always band stays
        self.assertNotIn("Termin 2T", values)
        self.assertNotIn("280W", values)

    def test_no_alarm_keeps_normal_selection(self):
        r = DashboardRenderer(max_items=5)
        r.add(DashboardItem("W", "21°C", priority=100, importance=90))
        r.add(DashboardItem("N", "Termin 2T", priority=500,
                            importance=45))

        self.assertEqual(len(r.select()), 2)


class AlertYamlTest(unittest.TestCase):

    def test_valid_alert_config(self):
        configs = build_widget_configs([{
            "type": "alert",
            "name": "Regen rein",
            "conditions": [
                {"entity": "binary_sensor.fenster", "state": "Offen"},
                {"entity": "sensor.regen", "above": 70},
            ],
        }])
        self.assertEqual(configs[0].name, "Regen rein")
        self.assertEqual(len(configs[0].conditions), 2)

    def test_conditions_must_not_be_empty(self):
        with self.assertRaises(ConfigError) as ctx:
            build_widget_configs([{
                "type": "alert",
                "name": "x",
                "conditions": [],
            }])
        self.assertIn("non-empty list", str(ctx.exception))

    def test_condition_needs_entity(self):
        with self.assertRaises(ConfigError) as ctx:
            build_widget_configs([{
                "type": "alert",
                "name": "x",
                "conditions": [{"state": "on"}],
            }])
        self.assertIn("missing 'entity'", str(ctx.exception))

    def test_condition_needs_criterion(self):
        with self.assertRaises(ConfigError) as ctx:
            build_widget_configs([{
                "type": "alert",
                "name": "x",
                "conditions": [{"entity": "sensor.x"}],
            }])
        self.assertIn("at least one criterion", str(ctx.exception))

    def test_unknown_condition_key(self):
        with self.assertRaises(ConfigError) as ctx:
            build_widget_configs([{
                "type": "alert",
                "name": "x",
                "conditions": [
                    {"entity": "sensor.x", "stat": "on"},
                ],
            }])
        self.assertIn("unknown option 'stat'", str(ctx.exception))

    def test_duration_must_be_numeric(self):
        with self.assertRaises(ConfigError) as ctx:
            build_widget_configs([{
                "type": "alert",
                "name": "x",
                "conditions": [
                    {"entity": "sensor.x", "state": "on",
                     "duration": "lange"},
                ],
            }])
        self.assertIn("'duration' must be a number", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
