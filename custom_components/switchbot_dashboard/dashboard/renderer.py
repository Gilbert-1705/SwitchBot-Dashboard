from ..const import MAX_ITEMS, MAX_VALUE_LENGTH, SEPARATOR
from ..text import shorten
from .item import DashboardItem


class DashboardRenderer:
    """Collects, prioritizes and renders dashboard items.

    Priority engine: from all visible items the ``max_items`` most
    important ones (highest importance) are selected and then shown
    in their configured order (priority).
    """

    def __init__(self, max_items: int = MAX_ITEMS):
        self.max_items = max_items
        self.items: list[DashboardItem] = []

    def add(self, item: DashboardItem):

        if item is not None:
            self.items.append(item)

    def select(self) -> list[DashboardItem]:
        """Selects the most important items."""

        visible = [
            item
            for item in self.items
            if item.visible
        ]

        selected = sorted(
            visible,
            key=lambda item: item.importance,
            reverse=True,
        )[: self.max_items]

        return sorted(
            selected,
            key=lambda item: item.priority,
        )

    def render(self):

        return SEPARATOR.join(
            f"{item.icon} {shorten(item.value, MAX_VALUE_LENGTH)}".strip()
            for item in self.select()
        )
