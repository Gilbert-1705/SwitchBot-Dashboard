"""Tests for restart-proof durations and the rounded power display.

Run (from the repo root):

    python3 custom_components/switchbot_dashboard/tests/test_tracker.py
"""

import asyncio
import unittest
from datetime import datetime, timedelta, timezone

import helpers  # noqa: F401  (stubs HA/aiohttp, sets sys.path)
from helpers import FakeHass, FakeState

from custom_components.switchbot_dashboard.const import DOMAIN
from custom_components.switchbot_dashboard.formatters.power import (
    PowerFormatter,
)
from custom_components.switchbot_dashboard.icons import Icons
from custom_components.switchbot_dashboard.tracker import (
    SinceTracker,
    state_since,
)
from custom_components.switchbot_dashboard.widgets.alert import AlertWidget
from custom_components.switchbot_dashboard.widgets.appliance import (
    ApplianceWidget,
)


def utc(**ago):
    return datetime.now(timezone.utc) - timedelta(**ago)


class FakeStore:
    """Stands in for homeassistant.helpers.storage.Store."""

    def __init__(self, data=None):
        self.data = data
        self.saves = 0

    async def async_load(self):
        return self.data

    def async_delay_save(self, data_func, delay):
        self.saves += 1
        self.data = dict(data_func())


class SinceTrackerTest(unittest.TestCase):

    def test_first_observation_uses_last_changed(self):
        tracker = SinceTracker()
        started = utc(hours=2)
        self.assertEqual(tracker.since("flag", "on", started), started)

    def test_restart_keeps_the_original_start(self):
        # Home Assistant re-stamps last_changed on restart
        tracker = SinceTracker()
        started = utc(hours=4)
        tracker.since("flag", "on", started)

        after_restart = utc(minutes=1)
        self.assertEqual(
            tracker.since("flag", "on", after_restart), started
        )

    def test_state_change_starts_a_new_period(self):
        tracker = SinceTracker()
        tracker.since("flag", "on", utc(hours=4))

        turned_off = utc(minutes=5)
        self.assertEqual(
            tracker.since("flag", "off", turned_off), turned_off
        )

    def test_old_start_is_not_reused_for_a_new_period(self):
        # on -> off -> on: the second "on" is a new reminder
        tracker = SinceTracker()
        tracker.since("flag", "on", utc(hours=6))
        tracker.since("flag", "off", utc(hours=1))

        again = utc(minutes=2)
        self.assertEqual(tracker.since("flag", "on", again), again)

    def test_changes_are_persisted(self):
        store = FakeStore()
        tracker = SinceTracker(store)
        tracker.since("flag", "on", utc(hours=1))

        self.assertEqual(store.saves, 1)
        self.assertEqual(store.data["flag"]["state"], "on")

    def test_unchanged_state_is_not_saved_again(self):
        store = FakeStore()
        tracker = SinceTracker(store)
        tracker.since("flag", "on", utc(hours=1))
        tracker.since("flag", "on", utc(minutes=1))

        self.assertEqual(store.saves, 1)

    def test_record_survives_a_restart_through_the_store(self):
        store = FakeStore()
        started = utc(hours=5)
        SinceTracker(store).since("flag", "on", started)

        # new process: a fresh tracker loads what was saved
        revived = SinceTracker(FakeStore(store.data))
        asyncio.run(revived.async_load())

        self.assertEqual(
            revived.since("flag", "on", utc(seconds=30)), started
        )

    def test_broken_stored_timestamp_is_replaced(self):
        tracker = SinceTracker(
            FakeStore({"flag": {"state": "on", "since": "kaputt"}})
        )
        asyncio.run(tracker.async_load())

        now = utc(seconds=5)
        self.assertEqual(tracker.since("flag", "on", now), now)


class StateSinceTest(unittest.TestCase):

    def test_without_tracker_falls_back_to_last_changed(self):
        changed = utc(minutes=7)
        state = FakeState("on", last_changed=changed)
        self.assertEqual(state_since(FakeHass({}), "x", state), changed)

    def test_missing_state(self):
        self.assertIsNone(state_since(FakeHass({}), "x", None))


def hass_with_tracker(states, tracker):
    hass = FakeHass(states)
    hass.data[DOMAIN] = {"tracker": tracker}
    return hass


class ReminderSurvivesRestartTest(unittest.TestCase):

    def _importance(self, hass):
        return ApplianceWidget(
            hass,
            name="WM",
            running_entity="status",
            done_entity="flag",
            icon=Icons.LAUNDRY,
        ).render().importance

    def test_done_reminder_keeps_its_level_after_a_restart(self):
        tracker = SinceTracker()

        # the flag was set four hours ago
        before = hass_with_tracker({
            "status": FakeState("stop", last_changed=utc(hours=4)),
            "flag": FakeState("on", last_changed=utc(hours=4)),
        }, tracker)
        self.assertEqual(self._importance(before), 95)

        # restart: every last_changed is re-stamped to "just now"
        after = hass_with_tracker({
            "status": FakeState("stop", last_changed=utc(seconds=20)),
            "flag": FakeState("on", last_changed=utc(seconds=20)),
        }, tracker)
        self.assertEqual(self._importance(after), 95)

    def test_without_tracker_the_reminder_would_start_over(self):
        # documents why the tracker exists
        hass = FakeHass({
            "status": FakeState("stop", last_changed=utc(seconds=20)),
            "flag": FakeState("on", last_changed=utc(seconds=20)),
        })
        self.assertEqual(self._importance(hass), 30)

    def test_new_reminder_after_reset_starts_quiet(self):
        tracker = SinceTracker()

        def render(flag, ago):
            hass = hass_with_tracker({
                "status": FakeState("stop", last_changed=utc(hours=9)),
                "flag": FakeState(flag, last_changed=ago),
            }, tracker)
            return ApplianceWidget(
                hass, name="WM", running_entity="status",
                done_entity="flag", icon=Icons.LAUNDRY,
            ).render()

        self.assertEqual(render("on", utc(hours=5)).importance, 95)
        self.assertIsNone(render("off", utc(hours=1)))
        self.assertEqual(render("on", utc(minutes=3)).importance, 30)


class AlertDurationSurvivesRestartTest(unittest.TestCase):

    CONDITIONS = [{"entity": "tuer", "state": "on", "duration": 600}]

    def _fires(self, hass):
        widget = AlertWidget(
            hass, name="Tür offen", conditions=self.CONDITIONS
        )
        return widget.render() is not None

    def test_duration_is_not_reset_by_a_restart(self):
        tracker = SinceTracker()

        before = hass_with_tracker(
            {"tuer": FakeState("on", last_changed=utc(minutes=30))},
            tracker,
        )
        self.assertTrue(self._fires(before))

        after = hass_with_tracker(
            {"tuer": FakeState("on", last_changed=utc(seconds=10))},
            tracker,
        )
        self.assertTrue(self._fires(after))

    def test_duration_condition_seen_even_if_an_earlier_one_fails(self):
        # the tracker must observe the door although "jan" already
        # fails the alert, otherwise a later period would start late
        tracker = SinceTracker()
        conditions = [
            {"entity": "jan", "not_state": "home"},
            {"entity": "tuer", "state": "on", "duration": 600},
        ]
        hass = hass_with_tracker({
            "jan": FakeState("home"),
            "tuer": FakeState("on", last_changed=utc(minutes=20)),
        }, tracker)

        AlertWidget(hass, name="x", conditions=conditions).render()

        self.assertIn("tuer", tracker._data)


class PowerRoundingTest(unittest.TestCase):

    def setUp(self):
        self.format = PowerFormatter().format

    def test_rounds_to_ten_watts(self):
        # real reading from the power meter
        self.assertEqual(self.format("318.216"), "320W")
        self.assertEqual(self.format("382"), "380W")

    def test_neighbouring_readings_give_the_same_text(self):
        # the point of rounding: small fluctuations do not change
        # the display line
        self.assertEqual(self.format("359"), self.format("362"))

    def test_small_values(self):
        self.assertEqual(self.format("4"), "0W")
        self.assertEqual(self.format("46"), "50W")

    def test_rounding_into_the_kilowatt_range(self):
        self.assertEqual(self.format("996"), "1.0kW")

    def test_kilowatts_unchanged(self):
        self.assertEqual(self.format("1234"), "1.2kW")
        self.assertEqual(self.format("12345"), "12kW")

    def test_invalid_value(self):
        self.assertEqual(self.format("unavailable"), "?")


if __name__ == "__main__":
    unittest.main()
