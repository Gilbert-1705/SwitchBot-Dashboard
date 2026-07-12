"""Tests for the appliance widget (washer/dryer).

Run (from the repo root):

    python3 custom_components/switchbot_dashboard/tests/test_appliance.py
"""

import unittest
from datetime import datetime, timedelta, timezone

import helpers  # noqa: F401  (stubs HA/aiohttp, sets sys.path)
from helpers import FakeHass, FakeState

from custom_components.switchbot_dashboard.icons import Icons
from custom_components.switchbot_dashboard.ramp import (
    time_based_importance,
)
from custom_components.switchbot_dashboard.widgets.appliance import (
    ApplianceWidget,
)


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
        # fresh done flag starts as a side note
        self.assertEqual(item.importance, 30)

    def test_running_is_background_info(self):
        item = self._render("on", "off")
        self.assertEqual(item.value, "WM läuft")
        self.assertEqual(item.importance, 15)

    def test_new_cycle_overrides_stale_done_flag(self):
        # A new cycle makes the old done reminder obsolete
        item = self._render("run", "on")
        self.assertEqual(item.value, "WM läuft")

    def test_done_shown_after_cycle_ends(self):
        item = self._render("stop", "on")
        self.assertEqual(item.value, "WM Fertig")

    def test_idle_and_emptied_is_hidden(self):
        self.assertIsNone(self._render("off", "off"))

    def test_run_state_shows_laeuft(self):
        item = self._render("run", "off")
        self.assertEqual(item.value, "WM läuft")

    def test_pause_state_shows_pause(self):
        item = self._render("pause", "off")
        self.assertEqual(item.value, "WM Pause")
        self.assertEqual(item.importance, 15)

    def test_stop_state_is_hidden(self):
        self.assertIsNone(self._render("stop", "off"))

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


class TimeRampTest(unittest.TestCase):

    STEPS = ((0, 30), (3600, 60), (10800, 100))

    def _importance(self, minutes_ago):
        now = datetime.now(timezone.utc)
        return time_based_importance(
            now - timedelta(minutes=minutes_ago),
            self.STEPS,
            now=now,
        )

    def test_fresh_is_side_note(self):
        self.assertEqual(self._importance(5), 30)

    def test_after_one_hour(self):
        self.assertEqual(self._importance(61), 60)

    def test_after_three_hours(self):
        self.assertEqual(self._importance(181), 100)

    def test_missing_timestamp_uses_first_step(self):
        self.assertEqual(
            time_based_importance(None, self.STEPS), 30
        )

    def test_done_reminder_ramps_up(self):
        three_hours_ago = (
            datetime.now(timezone.utc) - timedelta(hours=3, minutes=1)
        )
        hass = FakeHass({
            "laeuft": FakeState("stop"),
            "fertig": FakeState("on", last_changed=three_hours_ago),
        })
        item = ApplianceWidget(
            hass,
            name="WM",
            running_entity="laeuft",
            done_entity="fertig",
            icon=Icons.LAUNDRY,
        ).render()
        self.assertEqual(item.value, "WM Fertig")
        # capped at 95: loud, but never alarm mode
        self.assertEqual(item.importance, 95)


class QuietModeTest(unittest.TestCase):
    """Fillers never push the display beyond quiet_max_items."""

    def _renderer(self):
        from custom_components.switchbot_dashboard.dashboard import (
            DashboardRenderer,
        )
        from custom_components.switchbot_dashboard.dashboard.item import (
            DashboardItem,
        )
        self.DashboardItem = DashboardItem
        return DashboardRenderer(max_items=5, quiet_max_items=3)

    def test_quiet_day_stays_calm(self):
        r = self._renderer()
        I = self.DashboardItem
        r.add(I("W", "21°C", priority=100, importance=90))
        r.add(I("P", "280W", priority=200, importance=10))
        r.add(I("", "●", priority=250, importance=15))
        r.add(I("D", "Zu", priority=300, importance=20))

        selected = r.select()
        # 1 relevant + fillers up to the quiet limit of 3
        self.assertEqual(len(selected), 3)
        values = [i.value for i in selected]
        self.assertIn("21°C", values)
        self.assertNotIn("280W", values)  # weakest filler dropped

    def test_busy_day_uses_all_slots(self):
        r = self._renderer()
        I = self.DashboardItem
        for n, imp in enumerate((90, 85, 80, 65, 60, 10)):
            r.add(I("X", str(n), priority=n, importance=imp))

        selected = r.select()
        self.assertEqual(len(selected), 5)
        # the filler (10) is not among them
        self.assertNotIn("5", [i.value for i in selected])

    def test_fillers_only_shown_when_room_below_quiet_limit(self):
        r = self._renderer()
        I = self.DashboardItem
        r.add(I("A", "a", priority=1, importance=90))
        r.add(I("B", "b", priority=2, importance=70))
        r.add(I("C", "c", priority=3, importance=65))
        r.add(I("F", "f", priority=4, importance=10))

        # already 3 relevant items -> no filler on top
        self.assertEqual(len(r.select()), 3)


if __name__ == "__main__":
    unittest.main()
