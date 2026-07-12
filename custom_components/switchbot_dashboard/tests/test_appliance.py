"""Tests für das Haushaltsgeräte-Widget (Waschmaschine/Trockner).

Ausführen (vom Repo-Root):

    python3 custom_components/switchbot_dashboard/tests/test_appliance.py
"""

import unittest

import helpers  # noqa: F401  (stubbt HA/aiohttp, setzt sys.path)
from helpers import FakeHass, FakeState

from custom_components.switchbot_dashboard.icons import Icons
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
        self.assertEqual(item.importance, 80)

    def test_running_is_background_info(self):
        item = self._render("on", "off")
        self.assertEqual(item.value, "WM läuft")
        self.assertEqual(item.importance, 15)

    def test_new_cycle_overrides_stale_done_flag(self):
        # Läuft die Maschine wieder, ist der alte Reminder obsolet
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


if __name__ == "__main__":
    unittest.main()
