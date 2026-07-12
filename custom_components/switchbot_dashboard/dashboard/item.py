from dataclasses import dataclass


@dataclass(slots=True)
class DashboardItem:
    """A renderable dashboard element.

    priority   -> display order (lower = further left)
    importance -> how important is the information RIGHT NOW?
                  The dashboard only shows the most important items.

    Importance scale:
        100     warning, act immediately (e.g. locked but open)
        70-90   relevant today (waste today, birthday, door open)
        40-60   relevant soon (event in 2 days, window open)
        10-30   background info (power draw, everything closed)
    """

    icon: str
    value: str

    priority: int = 100

    importance: int = 0

    visible: bool = True
