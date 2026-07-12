from ..const import (
    IMPORTANCE_ALARM,
    IMPORTANCE_ALWAYS,
    IMPORTANCE_FILLER,
    MAX_ITEMS,
    MAX_VALUE_LENGTH,
    QUIET_MAX_ITEMS,
    SEPARATOR,
)
from ..text import shorten
from .item import DashboardItem


class DashboardRenderer:
    """Collects, prioritizes and renders dashboard items.

    Priority engine: from all visible items the ``max_items`` most
    important ones (highest importance) are selected and then shown
    in their configured order (priority).

    Quiet mode: filler items (importance <= IMPORTANCE_FILLER) never
    push the display beyond ``quiet_max_items``. On a busy day they
    are displaced anyway; on a calm day the display stays calm
    instead of filling every slot with background info.

    Alarm mode: as soon as any item reaches IMPORTANCE_ALARM (100),
    only alarms and always-band items (>= 60) are shown - normal
    items and fillers are displaced so the warning stands out.
    """

    def __init__(
        self,
        max_items: int = MAX_ITEMS,
        quiet_max_items: int = QUIET_MAX_ITEMS,
    ):
        self.max_items = max_items
        self.quiet_max_items = quiet_max_items
        self.items: list[DashboardItem] = []

    def add(self, item: DashboardItem):

        if item is not None:
            self.items.append(item)

    def select(self) -> list[DashboardItem]:
        """Selects the most important items."""

        visible = sorted(
            (item for item in self.items if item.visible),
            key=lambda item: (-item.importance, item.priority),
        )

        # Groups: only the most important item per group survives
        seen_groups: set[str] = set()
        deduped = []

        for item in visible:
            if item.group:
                if item.group in seen_groups:
                    continue
                seen_groups.add(item.group)
            deduped.append(item)

        visible = deduped

        # Alarm mode: a warning displaces everything non-essential
        if any(
            item.importance >= IMPORTANCE_ALARM for item in visible
        ):
            alarm_view = [
                item for item in visible
                if item.importance >= IMPORTANCE_ALWAYS
            ][: self.max_items]

            return sorted(
                alarm_view,
                key=lambda item: item.priority,
            )

        relevant = [
            item for item in visible
            if item.importance > IMPORTANCE_FILLER
        ]
        fillers = [
            item for item in visible
            if item.importance <= IMPORTANCE_FILLER
        ]

        selected = relevant[: self.max_items]

        # Fillers only top up to the quiet limit, never beyond
        quiet_limit = min(self.quiet_max_items, self.max_items)

        while fillers and len(selected) < quiet_limit:
            selected.append(fillers.pop(0))

        return sorted(
            selected,
            key=lambda item: item.priority,
        )

    def render(self):

        return SEPARATOR.join(
            f"{item.icon} {shorten(item.value, MAX_VALUE_LENGTH)}".strip()
            for item in self.select()
        )
