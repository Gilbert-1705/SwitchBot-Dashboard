"""Text helpers for the narrow e-paper display.

The display wraps the transmitted line itself at spaces
(pixel-based). Long widget texts displace other widgets, so every
widget keeps its text as compact as possible.
"""

ELLIPSIS = "…"


def shorten(value: str, max_length: int) -> str:
    """Hard-truncates a text to max_length including the ellipsis."""

    if max_length <= 0:
        return value

    if len(value) <= max_length:
        return value

    return value[: max_length - 1].rstrip() + ELLIPSIS


def cap_bytes(value: str, max_bytes: int) -> str:
    """Truncates a text to max_bytes (UTF-8) without splitting characters.

    The SwitchBot API rejects payloads over ~300 bytes with
    statusCode 190 ("invalid params"). Emojis take 4 bytes.
    """

    encoded = value.encode("utf-8")

    if len(encoded) <= max_bytes:
        return value

    # Cut at a character boundary
    truncated = encoded[:max_bytes]

    while truncated:
        try:
            return truncated.decode("utf-8")
        except UnicodeDecodeError:
            truncated = truncated[:-1]

    return ""


def state_text(value) -> str:
    """A configured state as Home Assistant spells it.

    YAML reads an unquoted ``on`` / ``off`` as a boolean. Compared as
    "True" it would never match the entity state "on" - and the
    widget would silently do nothing.
    """

    if value is True:
        return "on"

    if value is False:
        return "off"

    return str(value)


def join_names(names: list[str], max_names: int = 2) -> str:
    """Joins names compactly: 'A', 'A+B', 'A+2'."""

    if not names:
        return ""

    if len(names) <= max_names:
        return "+".join(names)

    shown = names[: max_names - 1]
    rest = len(names) - len(shown)

    return "+".join(shown) + f"+{rest}"
