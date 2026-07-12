"""Tests for widget groups and day context (v2.2).

Run (from the repo root):

    python3 custom_components/switchbot_dashboard/tests/test_context.py
"""

import unittest
from datetime import time

import helpers  # noqa: F401  (stubs HA/aiohttp, sets sys.path)
from helpers import FakeHass, FakeState

from custom_components.switchbot_dashboard.config.schema import (
    ConfigError,
    build_widget_configs,
)
from custom_components.switchbot_dashboard.context import (
    active_boost,
    apply_boost,
)
from custom_components.switchbot_dashboard.dashboard import (
    DashboardRenderer,
)
from custom_components.switchbot_dashboard.dashboard.item import (
    DashboardItem,
)
from custom_components.switchbot_dashboard.render import render_dashboard


class GroupDedupeTest(unittest.TestCase):

    def test_only_most_important_item_per_group(self):
        r = DashboardRenderer(max_items=5)
        r.add(DashboardItem("D", "Auf", priority=300, importance=60,
                            group="haus"))
        r.add(DashboardItem("F", "Gekippt", priority=250,
                            importance=40, group="haus"))
        r.add(DashboardItem("W", "21°C", priority=100, importance=90))

        values = [i.value for i in r.select()]

        self.assertIn("Auf", values)
        self.assertNotIn("Gekippt", values)
        self.assertIn("21°C", values)

    def test_tie_breaks_by_priority(self):
        r = DashboardRenderer(max_items=5)
        r.add(DashboardItem("A", "a", priority=200, importance=60,
                            group="g"))
        r.add(DashboardItem("B", "b", priority=100, importance=60,
                            group="g"))

        values = [i.value for i in r.select()]
        self.assertEqual(values, ["b"])

    def test_ungrouped_items_unaffected(self):
        r = DashboardRenderer(max_items=5)
        r.add(DashboardItem("A", "a", priority=1, importance=50))
        r.add(DashboardItem("B", "b", priority=2, importance=50))

        self.assertEqual(len(r.select()), 2)

    def test_alarm_in_group_displaces_siblings(self):
        r = DashboardRenderer(max_items=5)
        r.add(DashboardItem("!", "Haus", priority=50, importance=100,
                            group="haus"))
        r.add(DashboardItem("D", "Auf", priority=300, importance=60,
                            group="haus"))

        values = [i.value for i in r.select()]
        self.assertEqual(values, ["Haus"])


class ActiveBoostTest(unittest.TestCase):

    MORNING = [{"between": ["06:00", "09:00"], "add": 20}]

    def test_inside_window(self):
        self.assertEqual(
            active_boost(self.MORNING, now=time(7, 30)), 20
        )

    def test_outside_window(self):
        self.assertEqual(
            active_boost(self.MORNING, now=time(12, 0)), 0
        )

    def test_window_start_inclusive_end_exclusive(self):
        self.assertEqual(
            active_boost(self.MORNING, now=time(6, 0)), 20
        )
        self.assertEqual(
            active_boost(self.MORNING, now=time(9, 0)), 0
        )

    def test_midnight_wrap(self):
        night = [{"between": ["22:00", "06:00"], "add": 30}]
        self.assertEqual(active_boost(night, now=time(23, 30)), 30)
        self.assertEqual(active_boost(night, now=time(2, 0)), 30)
        self.assertEqual(active_boost(night, now=time(12, 0)), 0)

    def test_multiple_windows_add_up(self):
        boosts = [
            {"between": ["06:00", "09:00"], "add": 20},
            {"between": ["08:00", "10:00"], "add": 10},
        ]
        self.assertEqual(active_boost(boosts, now=time(8, 30)), 30)

    def test_negative_boost(self):
        night = [{"between": ["22:00", "06:00"], "add": -30}]
        self.assertEqual(active_boost(night, now=time(23, 0)), -30)


class ApplyBoostTest(unittest.TestCase):

    def test_boost_raises_importance(self):
        self.assertEqual(apply_boost(50, 20), 70)

    def test_boost_never_reaches_alarm(self):
        self.assertEqual(apply_boost(90, 50), 99)

    def test_negative_boost_clamped_at_zero(self):
        self.assertEqual(apply_boost(10, -30), 0)

    def test_alarm_is_untouched(self):
        self.assertEqual(apply_boost(100, -50), 100)


class PipelineTest(unittest.TestCase):
    """group and boost flow through manager -> render_dashboard."""

    def _configs(self, **extra):
        from custom_components.switchbot_dashboard.widgets import (
            config_models as cm,
        )
        return [
            cm.EntityWidgetConfig(
                type="entity", entity="a", icon="A",
                importance=50, group=extra.get("group", ""),
            ),
            cm.EntityWidgetConfig(
                type="entity", entity="b", icon="B",
                importance=40, group=extra.get("group", ""),
            ),
        ]

    def test_grouped_widgets_render_one_item(self):
        hass = FakeHass({"a": FakeState("1"), "b": FakeState("2")})
        line = render_dashboard(hass, self._configs(group="g"))
        self.assertEqual(line, "A 1")

    def test_ungrouped_widgets_render_both(self):
        hass = FakeHass({"a": FakeState("1"), "b": FakeState("2")})
        line = render_dashboard(hass, self._configs())
        self.assertEqual(line, "A 1   B 2")


class BoostYamlTest(unittest.TestCase):

    def test_valid_boost_config(self):
        configs = build_widget_configs([{
            "type": "waste",
            "entity": "sensor.muell",
            "boost": [
                {"between": ["06:00", "09:00"], "add": 20},
            ],
        }])
        self.assertEqual(configs[0].boost[0]["add"], 20)

    def test_group_option_on_any_widget(self):
        configs = build_widget_configs([
            {"type": "door", "group": "haus"},
            {
                "type": "window",
                "entities": {"a": "A"},
                "group": "haus",
            },
        ])
        self.assertEqual(configs[0].group, "haus")
        self.assertEqual(configs[1].group, "haus")

    def test_invalid_time_rejected(self):
        with self.assertRaises(ConfigError) as ctx:
            build_widget_configs([{
                "type": "waste",
                "entity": "sensor.muell",
                "boost": [
                    {"between": ["6 Uhr", "09:00"], "add": 20},
                ],
            }])
        self.assertIn("invalid time", str(ctx.exception))

    def test_between_needs_two_times(self):
        with self.assertRaises(ConfigError) as ctx:
            build_widget_configs([{
                "type": "waste",
                "entity": "sensor.muell",
                "boost": [{"between": ["06:00"], "add": 20}],
            }])
        self.assertIn("list of two times", str(ctx.exception))

    def test_unknown_boost_key(self):
        with self.assertRaises(ConfigError) as ctx:
            build_widget_configs([{
                "type": "waste",
                "entity": "sensor.muell",
                "boost": [
                    {"between": ["06:00", "09:00"], "plus": 20},
                ],
            }])
        self.assertIn("unknown option 'plus'", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
