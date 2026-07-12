from ..const import MAX_ITEMS
from .item import DashboardItem


class DashboardRenderer:
    """Collects, prioritizes and renders dashboard items.

    Priority Engine: Aus allen sichtbaren Items werden die
    ``max_items`` wichtigsten (höchste importance) ausgewählt und
    anschließend in ihrer konfigurierten Reihenfolge (priority)
    angezeigt.
    """

    def __init__(self, max_items: int = MAX_ITEMS):
        self.max_items = max_items
        self.items: list[DashboardItem] = []

    def add(self, item: DashboardItem):

        if item is not None:
            self.items.append(item)

    def select(self) -> list[DashboardItem]:
        """Wählt die wichtigsten Items aus."""

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

        return "   ".join(
            f"{item.icon} {item.value}".strip()
            for item in self.select()
        )
