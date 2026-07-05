from .item import DashboardItem

class DashboardRenderer:
    """Collects and renders dashboard items."""
    def __init__(self):
        self.items: list[DashboardItem] = []

    def add(self, item: DashboardItem):

        if item is not None:
            self.items.append(item)

    def render(self):

        self.items.sort(
            key=lambda x: x.priority,
        )

        return "   ".join(
            f"{item.icon} {item.value}"
            for item in self.items
        )