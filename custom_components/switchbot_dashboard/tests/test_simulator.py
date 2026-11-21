"""Tests for the display simulator, calibrated on photos of the device.

Run (from the repo root):

    python3 custom_components/switchbot_dashboard/tests/test_simulator.py
"""

import unittest

import helpers  # noqa: F401  (stubs HA/aiohttp, sets sys.path)

from custom_components.switchbot_dashboard.simulator import (
    LINE_WIDTH,
    MAX_LINES,
    NBSP,
    as_text_block,
    char_width,
    simulate,
    text_width,
)
from custom_components.switchbot_dashboard.text import keep_items_together

SEP = "   "


class PhotoCalibrationTest(unittest.TestCase):
    """The line breaks seen on the real panel (2026-11-21)."""

    def test_img_3486_icon_left_behind(self):
        # sent with plain spaces: the dryer icon stayed on line 1
        sim = simulate(
            "🌡 2°C ☀   🧺 WM Fertig   🧺 TR Fertig   🍽 GS Fertig"
        )
        self.assertEqual(sim.lines, [
            "🌡 2°C ☀   🧺 WM Fertig   🧺",
            "TR Fertig   🍽 GS Fertig",
        ])

    def test_img_3488_word_split(self):
        sim = simulate("🌡 2°C ☀   🚪 Zu   🍽 GS Fertig")
        self.assertEqual(sim.lines, ["🌡 2°C ☀   🚪 Zu   🍽 GS", "Fertig"])

    def test_img_3489_no_break_spaces(self):
        text = keep_items_together(
            "🌡 2°C ☀   🧺 WM Fertig   🧺 TR Fertig   🍽 GS Fertig   "
            "⛽ Tanken 1.98",
            SEP,
        )
        sim = simulate(text)
        self.assertEqual(sim.readable_lines(), [
            "🌡 2°C ☀   🧺 WM Fertig",
            "🧺 TR Fertig   🍽 GS Fertig",
            "⛽ Tanken 1.98",
        ])
        self.assertTrue(sim.fits)

    def test_measured_line_widths(self):
        # ink ends measured on IMG_3489, from the 28 px margin
        sim = simulate(keep_items_together(
            "🧺 TR Fertig   🍽 GS Fertig   ⛽ Tanken 1.98", SEP
        ))
        self.assertAlmostEqual(sim.widths[0], 694 - 28, delta=8)
        self.assertAlmostEqual(sim.widths[1], 420 - 28, delta=8)


class WrapRulesTest(unittest.TestCase):

    def test_empty_text_has_no_lines(self):
        self.assertEqual(simulate("").lines, [])
        self.assertTrue(simulate("").fits)

    def test_no_break_space_never_breaks(self):
        word = NBSP.join(["Fertig"] * 6)
        sim = simulate(f"A {word}")
        self.assertEqual(sim.lines, ["A", word])

    def test_spaces_at_the_break_are_dropped(self):
        sim = simulate("X" * 20 + "   " + "Y" * 5, line_width=500)
        self.assertEqual(sim.lines, ["X" * 20, "Y" * 5])

    def test_word_wider_than_a_line_is_reported(self):
        sim = simulate("W" * 30)
        self.assertEqual(len(sim.lines), 1)
        self.assertEqual(sim.too_wide, ["W" * 30])
        self.assertFalse(sim.fits)

    def test_too_many_lines_do_not_fit(self):
        items = SEP.join(["🧺" + NBSP + "Waschmaschine"] * 9)
        sim = simulate(items)
        self.assertGreater(len(sim.lines), MAX_LINES)
        self.assertFalse(sim.fits)

    def test_widths(self):
        self.assertEqual(char_width("🌡"), 60.0)
        self.assertEqual(char_width("🧺"), 73.0)
        self.assertEqual(char_width("⛽"), 73.0)
        self.assertEqual(char_width("️"), 0.0)
        # unknown characters count as wide
        self.assertEqual(char_width("一") >= 50, True)
        self.assertLess(text_width("Fertig"), LINE_WIDTH)

    def test_text_block_mentions_the_result(self):
        block = as_text_block(simulate("🌡 2°C ☀"))
        self.assertIn("🌡 2°C ☀", block)
        self.assertIn("fits", block)


class PreviewAttributesTest(unittest.TestCase):
    """The preview entity shows the predicted layout."""

    def test_publish_preview_adds_display_lines(self):
        from helpers import FakeHass
        from custom_components.switchbot_dashboard.render import (
            publish_preview,
        )

        hass = FakeHass({})
        publish_preview(
            hass,
            "🌡 2°C ☀   🧺 WM Fertig   🧺 TR Fertig   🍽 GS Fertig",
            sent=True,
        )
        _, attrs = hass.set_states["sensor.switchbot_dashboard"]
        self.assertEqual(attrs["display_lines"], [
            "🌡 2°C ☀   🧺 WM Fertig",
            "🧺 TR Fertig   🍽 GS Fertig",
        ])
        self.assertTrue(attrs["display_fits"])


if __name__ == "__main__":
    unittest.main()
