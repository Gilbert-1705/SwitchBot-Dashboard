"""Predicts how the Weather Station lays out the custom page.

The firmware wraps the transmitted line at spaces, left-aligned, in
the largest font size at which the text fits; a longer text is shown
in a smaller font. This module reproduces that, so line breaks and the
font size can be checked without the device.

Calibration (photos of the real panel, 2026-11-21):

    panel             800 x 480 px
    glyphs            Noto Sans CJK Regular advances at 54.6 px
                      (table in simulator_metrics.py)
    emojis            73 px, the thermometer 60 px
    full size         left margin 28 px, line width 744 px, pitch 84 px
    half size         everything 50 %, left margin about 20 px
                      (six lines of text, IMG_3539)

Verified: the line breaks of all reference photos, including the
effect of no-break spaces, and the switch to half size when the text
needs six lines at full size. Assumed: at most four lines fit at full
size; there may be sizes between full and half that no photo showed
yet.
"""

from dataclasses import dataclass, field

from .simulator_metrics import ADVANCES

PANEL_WIDTH = 800
PANEL_HEIGHT = 480
MARGIN_X = 28
LINE_WIDTH = 744
LINE_HEIGHT = 84
MAX_LINES = 4  # at full size; assumption, see module docstring
TEXT_HEIGHT = MAX_LINES * LINE_HEIGHT

# font sizes the firmware was seen using, largest first
SCALES = (1.0, 0.5)

EMOJI_WIDTH = 73.0
WIDTH_OVERRIDES = {
    "🌡": 60.0,
    "⌂": 44.0,  # measured at half size: 22 px
}

# characters the font does not have are drawn from the emoji set
EMOJI_RANGES = (
    (0x2600, 0x27BF),   # misc symbols, dingbats (☀ ☁ ☂ ⛽ ✈ ...)
    (0x2B00, 0x2BFF),
    (0x1F000, 0x1FAFF),
)

# confirmed on the device: these take their space but stay blank
NOT_RENDERED = {"🔋"}

# U+FE0F (emoji presentation) and ZWJ take no space of their own
ZERO_WIDTH = {"️", "︎", "‍"}

NBSP = " "


def char_width(char: str) -> float:
    """Advance of one character in device pixels."""

    if char in ZERO_WIDTH:
        return 0.0

    if char in WIDTH_OVERRIDES:
        return WIDTH_OVERRIDES[char]

    # symbols the font has (♪ ○ ⌂ ...) are drawn as text glyphs
    if char in ADVANCES:
        return ADVANCES[char]

    code = ord(char)

    for start, end in EMOJI_RANGES:
        if start <= code <= end:
            return EMOJI_WIDTH

    # unknown characters: assume the wider emoji size (errs on the
    # side of "does not fit")
    return ADVANCES.get(char, EMOJI_WIDTH)


def text_width(text: str) -> float:
    """Width at full size, in device pixels."""

    return sum(char_width(char) for char in text)


def margin(scale: float) -> float:
    """Left margin: 28 px at full size, about 20 px at half size."""

    return 12 + 16 * scale


def line_width(scale: float) -> float:
    return PANEL_WIDTH - 2 * margin(scale)


def nbsp_width(scale: float) -> float:
    """The no-break space does not shrink in proportion.

    Full size 12.2 px like a space, half size about 9.8 px instead of
    6.1 (IMG_3539: items with no-break spaces measured 5 % wider than
    their glyphs, while regular spaces scale normally).
    """

    return 7.4 + 4.8 * scale


@dataclass(slots=True)
class Simulation:
    """Result of laying out one display text."""

    lines: list[str] = field(default_factory=list)
    # in device pixels at the chosen font size
    widths: list[float] = field(default_factory=list)
    # words wider than a whole line (the firmware's behavior unknown)
    too_wide: list[str] = field(default_factory=list)
    # font size relative to the full size (1.0 or 0.5)
    scale: float = 1.0
    # even the smallest known size does not hold the text
    overflow: bool = False

    @property
    def fits(self) -> bool:
        """Shown in the full, readable font size."""

        return self.scale == 1.0 and not self.overflow

    @property
    def shrunk(self) -> bool:
        return self.scale < 1.0

    def readable_lines(self) -> list[str]:
        """Lines with no-break spaces shown as normal spaces."""

        return [line.replace(NBSP, " ") for line in self.lines]


def simulate(text: str, line_width_override: float | None = None) -> Simulation:
    """Lays out ``text`` like the firmware.

    Tries the font sizes from large to small and takes the first one
    at which the wrapped text fits the text area. With
    ``line_width_override`` only the full size is used (tests).
    """

    if not text.strip(" "):
        return Simulation()

    if line_width_override is not None:
        result = _wrap(text, 1.0, line_width_override)
        result.overflow = len(result.lines) > MAX_LINES or bool(result.too_wide)
        return result

    result = None

    for scale in SCALES:
        result = _wrap(text, scale, line_width(scale))

        height = len(result.lines) * LINE_HEIGHT * scale

        if height <= TEXT_HEIGHT and not result.too_wide:
            return result

    result.overflow = True
    return result


def _wrap(text: str, scale: float, width_limit: float) -> Simulation:
    """Greedy wrap at regular spaces; no-break spaces never break.

    The spaces at a line break are dropped, as on the device.
    """

    result = Simulation(scale=scale)
    line = ""
    pending_spaces = ""

    nbsp_extra = nbsp_width(scale) - ADVANCES[NBSP] * scale

    def width(value):
        return text_width(value) * scale + value.count(NBSP) * nbsp_extra

    for chunk in _chunks(text):

        if chunk.strip(" ") == "":
            pending_spaces += chunk
            continue

        candidate = line + pending_spaces + chunk if line else chunk

        if line and width(candidate) > width_limit:
            result.lines.append(line)
            line = chunk
        else:
            line = candidate

        pending_spaces = ""

        if width(chunk) > width_limit:
            result.too_wide.append(chunk)

    if line:
        result.lines.append(line)

    result.widths = [round(width(line), 1) for line in result.lines]

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
    limit = line_width(simulation.scale)

    for line, width in zip(simulation.readable_lines(), simulation.widths):
        fill = round(width / limit * 100)
        rows.append(f"│ {line}")
        rows.append(f"│   {width:5.0f} px  ({fill} % of the line)")

    rows.append(bottom)

    lines = len(simulation.lines)

    if simulation.overflow:
        status = "DOES NOT FIT, not even in the smallest font"
    elif simulation.shrunk:
        status = (
            f"font shrinks to {simulation.scale:.0%} - "
            "too long for the full size"
        )
    else:
        status = "full size, fits"

    rows.append(f"{lines} line{'s' if lines != 1 else ''} - {status}")

    blank = sorted({c for line in simulation.lines for c in line} & NOT_RENDERED)
    if blank:
        rows.append("not rendered by the device (blank): " + " ".join(blank))

    if simulation.too_wide:
        rows.append("too wide for one line: " + ", ".join(simulation.too_wide))

    return "\n".join(rows)
