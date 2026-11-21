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

    def test_img_3539_six_lines_shrink_the_font(self):
        # six items that each need a full-size line: the firmware
        # switched to half size, two items per line
        icons = ["○", "⌂", "♪", "🗑", "📅", "🔋"]
        text = keep_items_together(SEP.join(
            f"{icon} Zeile {n} von sechs" for n, icon in enumerate(icons, 1)
        ), SEP)
        sim = simulate(text)
        self.assertEqual(sim.scale, 0.5)
        self.assertEqual(sim.readable_lines(), [
            "○ Zeile 1 von sechs   ⌂ Zeile 2 von sechs",
            "♪ Zeile 3 von sechs   🗑 Zeile 4 von sechs",
            "📅 Zeile 5 von sechs   🔋 Zeile 6 von sechs",
        ])
        self.assertTrue(sim.shrunk)
        self.assertFalse(sim.fits)
        self.assertFalse(sim.overflow)
        # measured: "○ Zeile 1 … ⌂ Zeile 2 von sechs" ends at 551 px,
        # starting at the ~20 px margin
        self.assertAlmostEqual(sim.widths[0], 551 - 20, delta=12)

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
        word = NBSP.join(["Fertig"] * 3)
        sim = simulate(f"A {word}", line_width_override=500)
        self.assertEqual(sim.lines, ["A", word])

    def test_spaces_at_the_break_are_dropped(self):
        sim = simulate("X" * 20 + "   " + "Y" * 5, line_width_override=500)
        self.assertEqual(sim.lines, ["X" * 20, "Y" * 5])

    def test_word_too_wide_for_full_size_shrinks(self):
        sim = simulate("W" * 16)
        self.assertEqual(sim.scale, 0.5)
        self.assertEqual(len(sim.lines), 1)
        self.assertFalse(sim.fits)

    def test_word_too_wide_even_at_half_size_overflows(self):
        sim = simulate("W" * 40)
        self.assertTrue(sim.overflow)
        self.assertEqual(sim.too_wide, ["W" * 40])

    def test_four_lines_stay_full_size(self):
        items = SEP.join(["🧺" + NBSP + "Waschmaschine" + NBSP + "Fertig"] * 4)
        sim = simulate(items)
        self.assertEqual(len(sim.lines), MAX_LINES)
        self.assertEqual(sim.scale, 1.0)
        self.assertTrue(sim.fits)

    def test_five_lines_shrink(self):
        items = SEP.join(["🧺" + NBSP + "Waschmaschine" + NBSP + "Fertig"] * 5)
        sim = simulate(items)
        self.assertEqual(sim.scale, 0.5)
        self.assertFalse(sim.fits)

    def test_far_too_much_text_overflows(self):
        items = SEP.join(["🧺" + NBSP + "Waschmaschine" + NBSP + "Fertig"] * 30)
        self.assertTrue(simulate(items).overflow)

    def test_widths(self):
        self.assertEqual(char_width("🌡"), 60.0)
        self.assertEqual(char_width("🧺"), 73.0)
        self.assertEqual(char_width("⛽"), 73.0)
        # in the font: drawn as a text glyph, not as an emoji
        self.assertLess(char_width("♪"), 73.0)
        self.assertEqual(char_width("️"), 0.0)
        # unknown characters count as wide
        self.assertEqual(char_width("一") >= 50, True)
        self.assertLess(text_width("Fertig"), LINE_WIDTH)

    def test_text_block_mentions_the_result(self):
        block = as_text_block(simulate("🌡 2°C ☀"))
        self.assertIn("🌡 2°C ☀", block)
        self.assertIn("full size", block)

        shrunk = as_text_block(simulate(SEP.join(["🔋" + NBSP + "W" * 8] * 6)))
        self.assertIn("50%", shrunk)
        self.assertIn("not rendered", shrunk)


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
