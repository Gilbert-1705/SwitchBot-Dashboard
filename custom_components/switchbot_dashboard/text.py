"""Text-Hilfsfunktionen für das schmale E-Paper-Display.

Das Display bricht die gesendete Zeile selbst an Leerzeichen um
(pixelbasiert). Lange Widget-Texte verdrängen deshalb andere
Widgets — jedes Widget kürzt seinen Text so kompakt wie möglich.
"""

ELLIPSIS = "…"


def shorten(value: str, max_length: int) -> str:
    """Kürzt einen Text hart auf max_length inkl. Ellipse."""

    if max_length <= 0:
        return value

    if len(value) <= max_length:
        return value

    return value[: max_length - 1].rstrip() + ELLIPSIS


def join_names(names: list[str], max_names: int = 2) -> str:
    """Verbindet Namen kompakt: 'A', 'A+B', 'A+2'."""

    if not names:
        return ""

    if len(names) <= max_names:
        return "+".join(names)

    shown = names[: max_names - 1]
    rest = len(names) - len(shown)

    return "+".join(shown) + f"+{rest}"
