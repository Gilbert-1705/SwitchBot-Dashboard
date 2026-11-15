from dataclasses import dataclass


@dataclass(slots=True)
class DashboardItem:
    """A renderable dashboard element.

    priority   -> display order (lower = further left)
    importance -> how important is the information RIGHT NOW?
                  The dashboard only shows the most important items.

    Importance bands (constants in const.py):
        100     alarm, displaces everything non-essential
        60-99   always shown (within max_items)
        21-59   normal, competes for slots
        0-20    background info, quiet days only

    group -> items sharing a group compete: only the most
    important item of a group is displayed (e.g. door, window and
    alarm of the "haus" group render as one line).
    """

    icon: str
    value: str

    priority: int = 100

    importance: int = 0

    visible: bool = True

    group: str = ""

    # longest text of this item; 0 = the general limit
    max_length: int = 0
