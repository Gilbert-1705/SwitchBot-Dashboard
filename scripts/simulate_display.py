"""Shows how a dashboard line will look on the Weather Station.

    python3 scripts/simulate_display.py "🌡 2°C ☀   🧺 WM Fertig   🍽 GS Fertig"
    python3 scripts/simulate_display.py --png out.png "..."
    echo "..." | python3 scripts/simulate_display.py

The text is prepared exactly like the integration sends it (no-break
spaces inside items, see text.keep_items_together); --plain simulates
it as given. Line breaks come from the calibrated model in
custom_components/switchbot_dashboard/simulator.py. --png additionally
draws an 800x480 mock of the panel (needs Pillow; emojis appear as
boxes of their real width unless an emoji font is available).

The current line of a running installation is the state of
sensor.switchbot_dashboard; its attribute display_lines already holds
the same prediction.
"""

import argparse
import importlib
import sys
import types
import unicodedata
from pathlib import Path

PACKAGE_DIR = (
    Path(__file__).resolve().parent.parent
    / "custom_components" / "switchbot_dashboard"
)

# short hints drawn into the emoji boxes of the mock picture
EMOJI_LABELS = {
    "🌡": "TEMP", "☀": "SUN", "☁": "CLOUD", "☂": "RAIN", "🚪": "DOOR",
    "🗑": "BIN", "🧺": "BASKET", "🍽": "PLATE", "⛽": "FUEL", "🔋": "BATT",
    "🔌": "PLUG", "📅": "CAL", "🎂": "CAKE", "✈": "PLANE", "♪": "NOTE",
}

FONT_CANDIDATES = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
)


def _load_modules():
    """Imports simulator and text without the Home Assistant package."""

    package = types.ModuleType("sbd")
    package.__path__ = [str(PACKAGE_DIR)]
    sys.modules["sbd"] = package
    simulator = importlib.import_module("sbd.simulator")
    text = importlib.import_module("sbd.text")
    const = importlib.import_module("sbd.const")
    return simulator, text, const


def render_png(simulator, simulation, path, font_path=None):
    from PIL import Image, ImageDraw, ImageFont

    font_file = font_path or next(
        (f for f in FONT_CANDIDATES if Path(f).exists()), None
    )
    size = round(simulator.ADVANCES["F"] / 0.53)  # glyph size from metrics
    font = (
        ImageFont.truetype(font_file, size) if font_file
        else ImageFont.load_default()
    )
    small = (
        ImageFont.truetype(font_file, 26) if font_file
        else ImageFont.load_default()
    )
    tiny = (
        ImageFont.truetype(font_file, 13) if font_file
        else ImageFont.load_default()
    )

    image = Image.new("L", (simulator.PANEL_WIDTH, simulator.PANEL_HEIGHT), 214)
    draw = ImageDraw.Draw(image)

    # header and footer like the firmware draws them
    draw.text((28, 22), "10:05     5/3°C", fill=40, font=small)
    footer_top = 433
    draw.rectangle((0, footer_top, simulator.PANEL_WIDTH, 480), fill=25)
    draw.text((110, 444), "Zuhause", fill=200, font=small)
    draw.text((330, 444), "Tages-Zeitplan", fill=200, font=small)

    # text block, vertically centred between header and footer
    header_bottom = 75
    lines = simulation.lines
    block = len(lines) * simulator.LINE_HEIGHT
    top = header_bottom + max(0, (footer_top - header_bottom - block) // 2)

    for row, line in enumerate(lines):
        x = simulator.MARGIN_X
        y = top + row * simulator.LINE_HEIGHT

        for char in line:
            width = simulator.char_width(char)
            if width == simulator.EMOJI_WIDTH or char in simulator.WIDTH_OVERRIDES:
                draw.rounded_rectangle(
                    (x + 4, y + 14, x + width - 4, y + 70),
                    radius=8, outline=30, width=3,
                )
                # emoji name as a hint, e.g. "BASKET"
                label = EMOJI_LABELS.get(
                    char, unicodedata.name(char, "?").split()[-1][:6]
                )
                draw.text(
                    (x + width / 2, y + 42), label, fill=30, font=tiny,
                    anchor="mm",
                )
            elif char not in (" ", simulator.NBSP):
                # stroke imitates the heavier firmware font without
                # changing the calibrated advances
                draw.text(
                    (x, y), char, fill=20, font=font,
                    stroke_width=1, stroke_fill=20,
                )
            x += width

        if x - simulator.MARGIN_X > simulator.LINE_WIDTH:
            draw.line((x, y + 10, x, y + 74), fill=0, width=3)

    # usable area
    right = simulator.MARGIN_X + simulator.LINE_WIDTH
    draw.line((right, header_bottom, right, footer_top), fill=150, width=1)

    image.save(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("text", nargs="?", help="dashboard line (or stdin)")
    parser.add_argument("--png", help="also write a mock picture")
    parser.add_argument("--font", help="font file for --png")
    parser.add_argument(
        "--plain", action="store_true",
        help="do not protect the spaces inside items",
    )
    args = parser.parse_args(argv)

    text = args.text if args.text is not None else sys.stdin.read().strip()

    simulator, text_module, const = _load_modules()

    if not args.plain:
        text = text_module.keep_items_together(text, const.SEPARATOR)

    simulation = simulator.simulate(text)
    print(simulator.as_text_block(simulation))

    if args.png:
        render_png(simulator, simulation, args.png, args.font)
        print(f"picture: {args.png}")

    return 0 if simulation.fits else 1


if __name__ == "__main__":
    sys.exit(main())
