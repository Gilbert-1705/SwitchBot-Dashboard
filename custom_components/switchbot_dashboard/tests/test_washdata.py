"""Tests for the appliance widget with WashData-style status entities.

WashData detects state and phase from power consumption. Its state
sensor reports e.g. off / starting / running / paused / delay_wait /
interrupted / clean - and stays ``clean`` until the appliance is
marked as unloaded, so no manual done flag is needed.

Run (from the repo root):

    python3 custom_components/switchbot_dashboard/tests/test_washdata.py
"""

import unittest
from datetime import datetime, timedelta, timezone

import helpers  # noqa: F401  (stubs HA/aiohttp, sets sys.path)
from helpers import FakeHass, FakeState

from custom_components.switchbot_dashboard.config.schema import (
    build_widget_configs,
)
from custom_components.switchbot_dashboard.icons import Icons
from custom_components.switchbot_dashboard.updater import collect_entities
from custom_components.switchbot_dashboard.widgets.appliance import (
    ApplianceWidget,
)


def render(state, phase=None, remaining=None, last_changed=None):

    states = {"zustand": FakeState(state, last_changed=last_changed)}

    if phase is not None:
        states["phase"] = FakeState(phase)

    if remaining is not None:
        states["rest"] = FakeState(remaining)

    return ApplianceWidget(
        FakeHass(states),
        name="GS",
        running_entity="zustand",
        remaining_entity="rest",
        phase_entity="phase",
        icon=Icons.DISHWASHER,
    ).render()


class WashDataStatesTest(unittest.TestCase):

    def test_off_and_idle_are_hidden(self):
        self.assertIsNone(render("off"))
        self.assertIsNone(render("idle"))
        self.assertIsNone(render("unknown"))

    def test_running_without_details(self):
        item = render("running")
        self.assertEqual(item.value, "GS läuft")
        self.assertEqual(item.icon, Icons.DISHWASHER)
        self.assertEqual(item.importance, 30)

    def test_starting_and_ending_count_as_running(self):
        self.assertEqual(render("starting").value, "GS läuft")
        self.assertEqual(render("ending").value, "GS läuft")

    def test_clean_is_done_without_helper(self):
        item = render("clean")
        self.assertEqual(item.value, "GS Fertig")
        self.assertEqual(item.importance, 30)

    def test_finished_and_anti_wrinkle_are_done(self):
        self.assertEqual(render("finished").value, "GS Fertig")
        self.assertEqual(render("anti_wrinkle").value, "GS Fertig")

    def test_done_reminder_ramps_with_time_in_clean(self):
        long_ago = (
            datetime.now(timezone.utc) - timedelta(hours=3, minutes=5)
        )
        item = render("clean", last_changed=long_ago)
        self.assertEqual(item.importance, 95)

    def test_paused(self):
        self.assertEqual(render("paused").value, "GS Pause")
        self.assertEqual(render("user_paused").value, "GS Pause")

    def test_delayed_start(self):
        item = render("delay_wait")
        self.assertEqual(item.value, "GS wartet")
        self.assertEqual(item.importance, 15)

    def test_interrupted_needs_attention(self):
        item = render("interrupted")
        self.assertEqual(item.value, "GS Abbruch")
        self.assertEqual(item.importance, 65)
        self.assertEqual(render("force_stopped").value, "GS Abbruch")


class QuietDayVisibilityTest(unittest.TestCase):
    """Regression: found by rendering against real sensor values.

    On a quiet day the display shows weather plus fillers ("door
    closed", "windows closed"). A running dishwasher used to be a
    filler as well and lost against them - it never showed up.
    """

    def test_running_appliance_wins_a_slot_on_a_quiet_day(self):
        from custom_components.switchbot_dashboard.dashboard import (
            DashboardRenderer,
        )
        from custom_components.switchbot_dashboard.dashboard.item import (
            DashboardItem,
        )

        r = DashboardRenderer(max_items=5, quiet_max_items=3)
        r.add(DashboardItem("W", "0°C", priority=100, importance=90))
        r.add(DashboardItem("P", "318W", priority=200, importance=10))
        r.add(DashboardItem("", "●", priority=250, importance=15))
        r.add(DashboardItem("D", "Zu", priority=300, importance=20))
        r.add(DashboardItem("H", "Jan", priority=600, importance=15))
        r.add(render("running", phase="Klarspülen 69"))

        values = [item.value for item in r.select()]

        self.assertIn("GS Klarspülen", values)
        self.assertEqual(len(values), 3)


class RunningDetailTest(unittest.TestCase):

    def test_phase_is_shown(self):
        item = render("running", phase="Trocknen", remaining="42")
        self.assertEqual(item.value, "GS Trocknen")

    def test_temperature_suffix_is_stripped_from_phase(self):
        # real WashData phase names: "Klarspülen 69", "Reinigen 45"
        item = render("running", phase="Klarspülen 69")
        self.assertEqual(item.value, "GS Klarspülen")
        item = render("running", phase="Reinigen 45")
        self.assertEqual(item.value, "GS Reinigen")

    def test_unknown_phase_falls_back_to_remaining(self):
        item = render("running", phase="unknown", remaining="42")
        # rounded up to 5-minute steps: fewer e-paper refreshes
        self.assertEqual(item.value, "GS 45min")

    def test_remaining_exact_step_is_kept(self):
        item = render("running", remaining="40")
        self.assertEqual(item.value, "GS 40min")

    def test_unknown_remaining_falls_back_to_laeuft(self):
        item = render("running", phase="unknown", remaining="unknown")
        self.assertEqual(item.value, "GS läuft")

    def test_zero_remaining_falls_back_to_laeuft(self):
        item = render("running", remaining="0")
        self.assertEqual(item.value, "GS läuft")


class DoneFlagStillWorksTest(unittest.TestCase):
    """The manual input_boolean flag keeps working alongside."""

    def test_flag_and_simple_sensor(self):
        hass = FakeHass({
            "status": FakeState("stop"),
            "flag": FakeState("on"),
        })
        item = ApplianceWidget(
            hass,
            name="WM",
            running_entity="status",
            done_entity="flag",
        ).render()
        self.assertEqual(item.value, "WM Fertig")
        # default icon when none is configured
        self.assertEqual(item.icon, Icons.LAUNDRY)


class WashDataConfigTest(unittest.TestCase):

    def test_yaml_without_done_entity(self):
        configs = build_widget_configs([{
            "type": "appliance",
            "name": "GS",
            "running_entity": "sensor.geschirrspuler_zustand",
            "remaining_entity": "sensor.geschirrspuler_verbleibende_zeit",
            "phase_entity": "sensor.geschirrspuler_aktuelle_phase",
            "icon": "🍽",
        }])
        self.assertEqual(configs[0].done_entity, "")
        self.assertEqual(
            configs[0].phase_entity,
            "sensor.geschirrspuler_aktuelle_phase",
        )

    def test_all_entities_are_watched_by_the_updater(self):
        configs = build_widget_configs([{
            "type": "appliance",
            "name": "GS",
            "running_entity": "sensor.zustand",
            "remaining_entity": "sensor.rest",
            "phase_entity": "sensor.phase",
        }])
        self.assertEqual(
            collect_entities(configs),
            {"sensor.zustand", "sensor.rest", "sensor.phase"},
        )


if __name__ == "__main__":
    unittest.main()
