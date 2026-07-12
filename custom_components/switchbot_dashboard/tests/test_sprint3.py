"""Tests for sprint 3: smart door, calendar, window 2.0, priority engine.

Run (from the repo root):

    python3 custom_components/switchbot_dashboard/tests/test_sprint3.py
"""

import unittest
from datetime import date, timedelta

import helpers  # noqa: F401  (stubs HA/aiohttp, sets sys.path)
from helpers import FakeHass, FakeState

from custom_components.switchbot_dashboard.config.entities import Entities
from custom_components.switchbot_dashboard.dashboard.item import DashboardItem
from custom_components.switchbot_dashboard.dashboard.renderer import (
    DashboardRenderer,
)
from custom_components.switchbot_dashboard.icons import Icons
from custom_components.switchbot_dashboard.widgets.calendar import (
    CalendarWidget,
)
from custom_components.switchbot_dashboard.widgets.door import DoorWidget
from custom_components.switchbot_dashboard.widgets.window import WindowWidget


class DoorWidgetTest(unittest.TestCase):

    def _render(self, lock, contact):
        hass = FakeHass({
            Entities.DOOR_LOCK: FakeState(lock),
            Entities.DOOR_CONTACT: FakeState(contact),
        })
        return DoorWidget(hass).render()

    def test_locked_and_closed(self):
        item = self._render("locked", "off")
        self.assertEqual(item.value, "Zu")
        self.assertEqual(item.icon, Icons.DOOR)

    def test_unlocked_and_closed(self):
        item = self._render("unlocked", "off")
        self.assertEqual(item.value, "Auf")

    def test_unlocked_and_open(self):
        item = self._render("unlocked", "on")
        self.assertEqual(item.value, "Offen")
        self.assertEqual(item.icon, Icons.DOOR)

    def test_locked_but_open_is_warning(self):
        item = self._render("locked", "on")
        self.assertEqual(item.value, "Offen")
        self.assertEqual(item.icon, Icons.WARNING)
        self.assertEqual(item.importance, 100)

    def test_unavailable_hides_widget(self):
        self.assertIsNone(self._render("unavailable", "off"))
        self.assertIsNone(self._render("locked", "unknown"))


class WindowWidgetTest(unittest.TestCase):

    ENTITIES = {
        "fenster_wohnen": "Wohnen",
        "fenster_essen": "Essen",
    }

    def _render(self, wohnen, essen):
        hass = FakeHass({
            "fenster_wohnen": FakeState(wohnen),
            "fenster_essen": FakeState(essen),
        })
        return WindowWidget(hass, entities=self.ENTITIES).render()

    def test_all_closed(self):
        item = self._render("off", "off")
        self.assertEqual(item.value, Icons.CLOSED)

    def test_one_open_shows_room_name(self):
        item = self._render("on", "off")
        self.assertEqual(item.icon, Icons.OPEN)
        self.assertEqual(item.value, "Wohnen")

    def test_two_open_joined_with_plus(self):
        item = self._render("on", "on")
        self.assertEqual(item.value, "Wohnen+Essen")


class CalendarWidgetTest(unittest.TestCase):

    def _render(self, start, message="Oma", days=3):
        hass = FakeHass({
            "kalender": FakeState(
                "off",
                {"message": message, "start_time": start},
            ),
        })
        return CalendarWidget(
            hass,
            entity="kalender",
            icon=Icons.BIRTHDAY,
            days=days,
        ).render()

    def test_today_shows_name_only(self):
        item = self._render(date.today().isoformat())
        self.assertEqual(item.value, "Oma")
        self.assertEqual(item.icon, Icons.BIRTHDAY)

    def test_tomorrow(self):
        start = (date.today() + timedelta(days=1)).isoformat()
        item = self._render(start)
        self.assertEqual(item.value, "Oma Morgen")

    def test_in_three_days(self):
        start = (date.today() + timedelta(days=3)).isoformat()
        item = self._render(start)
        self.assertEqual(item.value, "Oma 3T")

    def test_outside_lookahead_is_hidden(self):
        start = (date.today() + timedelta(days=5)).isoformat()
        self.assertIsNone(self._render(start))

    def test_datetime_format_is_parsed(self):
        start = f"{date.today().isoformat()} 09:00:00"
        item = self._render(start)
        self.assertEqual(item.value, "Oma")

    def test_no_event_is_hidden(self):
        hass = FakeHass({"kalender": FakeState("off", {})})
        widget = CalendarWidget(
            hass, entity="kalender", icon=Icons.BIRTHDAY
        )
        self.assertIsNone(widget.render())


class PriorityEngineTest(unittest.TestCase):

    def test_selects_most_important_items(self):

        renderer = DashboardRenderer(max_items=2)

        renderer.add(DashboardItem("A", "1", priority=10, importance=10))
        renderer.add(DashboardItem("B", "2", priority=20, importance=90))
        renderer.add(DashboardItem("C", "3", priority=30, importance=50))

        selected = renderer.select()

        self.assertEqual(len(selected), 2)
        self.assertEqual([i.icon for i in selected], ["B", "C"])

    def test_display_order_follows_priority(self):

        renderer = DashboardRenderer(max_items=5)

        renderer.add(DashboardItem("B", "2", priority=200, importance=90))
        renderer.add(DashboardItem("A", "1", priority=100, importance=10))

        self.assertEqual(renderer.render(), "A 1   B 2")

    def test_invisible_items_are_skipped(self):

        renderer = DashboardRenderer()

        renderer.add(
            DashboardItem("A", "1", importance=100, visible=False)
        )
        renderer.add(DashboardItem("B", "2", importance=10))

        self.assertEqual(renderer.render(), "B 2")

    def test_iconless_item_has_no_leading_space(self):

        renderer = DashboardRenderer()
        renderer.add(DashboardItem("", "●", importance=10))

        self.assertEqual(renderer.render(), "●")


if __name__ == "__main__":
    unittest.main()
