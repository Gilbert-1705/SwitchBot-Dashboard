"""Predicts how the Weather Station lays out the custom page.

The firmware takes the transmitted line, renders it in one fixed font
size and wraps it at spaces, left-aligned. This module reproduces
that, so line breaks and overflow can be checked without the device.

Calibration (photos of the real panel, 2026-11-21, IMG_3486/3488/3489):

    panel             800 x 480 px
    glyphs            Noto Sans CJK Regular advances at 54.6 px
                      (table in simulator_metrics.py)
    emojis            73 px, the thermometer 60 px
    left margin       28 px, usable line width 744 px
    line pitch        84 px

Verified: the line breaks of all three photos, including the effect of
no-break spaces. Assumed, not yet seen on the device: at most four
lines fit between header and footer; what the firmware does beyond
that (cut off or shrink) is unknown, so overflow is only reported.
"""

from dataclasses import dataclass, field

from .simulator_metrics import ADVANCES

PANEL_WIDTH = 800
PANEL_HEIGHT = 480
MARGIN_X = 28
LINE_WIDTH = 744
LINE_HEIGHT = 84
MAX_LINES = 4  # assumption, see module docstring

EMOJI_WIDTH = 73.0
WIDTH_OVERRIDES = {
    "🌡": 60.0,
}

# characters the font does not have are drawn from the emoji set
EMOJI_RANGES = (
    (0x2600, 0x27BF),   # misc symbols, dingbats (☀ ☁ ☂ ⛽ ✈ ...)
    (0x2B00, 0x2BFF),
    (0x1F000, 0x1FAFF),
)

# U+FE0F (emoji presentation) and ZWJ take no space of their own
ZERO_WIDTH = {"️", "︎", "‍"}

NBSP = " "


def char_width(char: str) -> float:
    """Advance of one character in device pixels."""

    if char in ZERO_WIDTH:
        return 0.0

    if char in WIDTH_OVERRIDES:
        return WIDTH_OVERRIDES[char]

    code = ord(char)

    for start, end in EMOJI_RANGES:
        if start <= code <= end:
            return EMOJI_WIDTH

    # unknown characters: assume the wider emoji size (errs on the
    # side of "does not fit")
    return ADVANCES.get(char, EMOJI_WIDTH)


def text_width(text: str) -> float:
    return sum(char_width(char) for char in text)


@dataclass(slots=True)
class Simulation:
    """Result of laying out one display text."""

    lines: list[str] = field(default_factory=list)
    widths: list[float] = field(default_factory=list)
    # words wider than a whole line (the firmware's behavior unknown)
    too_wide: list[str] = field(default_factory=list)

    @property
    def fits(self) -> bool:
        return len(self.lines) <= MAX_LINES and not self.too_wide

    def readable_lines(self) -> list[str]:
        """Lines with no-break spaces shown as normal spaces."""

        return [line.replace(NBSP, " ") for line in self.lines]


def simulate(text: str, line_width: float = LINE_WIDTH) -> Simulation:
    """Wraps ``text`` like the firmware: greedy, at regular spaces.

    No-break spaces never break. The spaces at a line break are
    dropped, as on the device.
    """

    result = Simulation()

    if not text.strip(" "):
        return result

    line = ""
    pending_spaces = ""

    for chunk in _chunks(text):

        if chunk.strip(" ") == "":
            pending_spaces += chunk
            continue

        candidate = line + pending_spaces + chunk if line else chunk

        if line and text_width(candidate) > line_width:
            result.lines.append(line)
            line = chunk
        else:
            line = candidate

        pending_spaces = ""

        if text_width(chunk) > line_width:
            result.too_wide.append(chunk)

    if line:
        result.lines.append(line)

    result.widths = [round(text_width(line), 1) for line in result.lines]

    return result


def _chunks(text: str):
    """Splits into words and runs of regular spaces (NBSP stays in words)."""

    current = ""
    in_spaces = False

    for char in text:
        is_space = char == " "

        if current and is_space != in_spaces:
            yield current
            current = ""

        current += char
        in_spaces = is_space

    if current:
        yield current


def as_text_block(simulation: Simulation) -> str:
    """ASCII picture of the panel area, for logs and the CLI."""

    inner = 46
    top = "┌" + "─" * inner + "┐"
    bottom = "└" + "─" * inner + "┘"
    rows = [top]

    for line, width in zip(simulation.readable_lines(), simulation.widths):
        fill = round(width / LINE_WIDTH * 100)
        rows.append(f"│ {line}")
        rows.append(f"│   {width:5.0f} px  ({fill} % of the line)")

    rows.append(bottom)

    status = "fits" if simulation.fits else "DOES NOT FIT"
    rows.append(
        f"{len(simulation.lines)} of max. {MAX_LINES} lines - {status}"
    )

    if simulation.too_wide:
        rows.append("too wide for one line: " + ", ".join(simulation.too_wide))

    return "\n".join(rows)
