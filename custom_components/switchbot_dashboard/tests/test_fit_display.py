"""Tests for leaving out items when the text is too long for the panel.

Run (from the repo root):

    python3 custom_components/switchbot_dashboard/tests/test_fit_display.py
"""

import unittest

import helpers  # noqa: F401  (stubs HA/aiohttp, sets sys.path)

from custom_components.switchbot_dashboard.config.schema import ConfigError
from custom_components.switchbot_dashboard.dashboard.item import DashboardItem
from custom_components.switchbot_dashboard.dashboard.renderer import (
    DashboardRenderer,
    fit_to_display,
    join_items,
)
from custom_components.switchbot_dashboard.settings import settings_from_yaml
from custom_components.switchbot_dashboard.simulator import simulate
from custom_components.switchbot_dashboard.text import keep_items_together


def item(value, importance, priority, icon="🧺"):
    return DashboardItem(
        icon=icon, value=value, importance=importance, priority=priority,
    )


def layout(items):
    return simulate(keep_items_together(join_items(items), "   "))


# six items that need six full-size lines: the panel would halve the font
LONG = [
    item("Waschmaschine", 30, 100),
    item("Trockner Fertig", 60, 200),
    item("Spülmaschine", 45, 300),
    item("Waschmaschine", 30, 400),
    item("Trockner Fertig", 95, 500),
    item("Spülmaschine", 45, 600),
]


class FitToDisplayTest(unittest.TestCase):

    def test_short_text_is_untouched(self):
        items = [item("WM Fertig", 30, 100), item("GS Fertig", 30, 200)]
        self.assertEqual(fit_to_display(items), items)

    def test_long_text_loses_the_least_important_items(self):
        self.assertFalse(layout(LONG).fits)

        kept = fit_to_display(LONG)

        self.assertTrue(layout(kept).fits)
        self.assertLess(len(kept), len(LONG))
        # the two least important (30) go first, the rightmost first
        dropped = [i for i in LONG if i not in kept]
        self.assertEqual(dropped[0].importance, 30)
        self.assertIn(LONG[4], kept)   # importance 95 stays
        # display order is kept
        self.assertEqual(kept, sorted(kept, key=lambda i: i.priority))

    def test_equal_importance_drops_the_rightmost(self):
        items = [item("Waschmaschine Fertig", 30, p) for p in (1, 2, 3, 4, 5, 6)]
        kept = fit_to_display(items)
        self.assertEqual(kept, items[: len(kept)])

    def test_alarms_are_never_dropped(self):
        alarms = [item("Balkon offen jetzt", 100, p, icon="!") for p in range(6)]
        kept = fit_to_display(alarms)
        self.assertEqual(kept, alarms)
        self.assertFalse(layout(kept).fits)   # small print, but shown

    def test_a_single_item_always_stays(self):
        huge = [item("W" * 30, 30, 1)]
        self.assertEqual(fit_to_display(huge), huge)


class RendererOptionTest(unittest.TestCase):

    def _render(self, fit):
        renderer = DashboardRenderer(max_items=10, quiet_max_items=10,
                                     fit_display=fit)
        for i in LONG:
            renderer.add(DashboardItem(
                icon=i.icon, value=i.value, importance=i.importance,
                priority=i.priority,
            ))
        return renderer.render()

    def test_fit_display_on_by_default(self):
        self.assertTrue(DashboardRenderer().fit_display)
        text = self._render(fit=True)
        self.assertTrue(simulate(keep_items_together(text, "   ")).fits)

    def test_fit_display_off_keeps_everything(self):
        text = self._render(fit=False)
        self.assertEqual(text.count("🧺"), 6)
        self.assertFalse(simulate(keep_items_together(text, "   ")).fits)


class SettingsTest(unittest.TestCase):

    def test_default_and_yaml(self):
        self.assertTrue(settings_from_yaml({}).fit_display)
        self.assertFalse(settings_from_yaml({"fit_display": False}).fit_display)

    def test_must_be_a_boolean(self):
        with self.assertRaises(ConfigError):
            settings_from_yaml({"fit_display": "maybe"})


if __name__ == "__main__":
    unittest.main()
