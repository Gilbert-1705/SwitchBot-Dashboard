import logging

from .base import BaseWidget, DashboardItem
from ..icons import Icons

_LOGGER = logging.getLogger(__name__)


class FuelWidget(BaseWidget):
    """Fuel level with a refuel recommendation.

    Combines tank level and current fuel price (EUR/l) with two
    thresholds:

        min_level  -> below this the level becomes relevant
        max_price  -> up to this price refueling is worth it

    The level can be in percent (unit="%", default) or liters
    (unit="l"); min_level uses the same unit.

    States:

        level low AND price good  -> "⛽ Tanken 1.65"  (important)
        level low                 -> "⛽ 15%"
        price good, half empty    -> "⛽ 1.65"          (hint)
        otherwise                 -> hidden
    """

    def __init__(
        self,
        hass,
        level_entity: str,
        price_entity: str,
        min_level: float = 20.0,
        max_price: float = 1.75,
        unit: str = "%",
        priority: int = 610,
    ):
        super().__init__(hass)

        self.level_entity = level_entity
        self.price_entity = price_entity
        self.min_level = min_level
        self.max_price = max_price
        self.unit = "%" if unit == "%" else "L"
        self.priority = priority

    def render(self):

        level = self._number(self.level_entity)
        price = self._number(self.price_entity)

        if level is None and price is None:
            return None

        level_low = level is not None and level <= self.min_level
        price_good = price is not None and price <= self.max_price

        if level_low and price_good:
            value = f"Tanken {price:.2f}"
            importance = 85

        elif level_low:
            value = f"{level:.0f}{self.unit}"
            importance = 65

        elif price_good and level is not None and level <= self.min_level * 2:
            # Price is good and the tank is no longer full -
            # a cheap opportunity, but not a must
            value = f"{price:.2f}"
            importance = 40

        else:
            return None

        return DashboardItem(
            icon=Icons.FUEL,
            value=value,
            priority=self.priority,
            importance=importance,
        )

    def _number(self, entity: str) -> float | None:

        state = self.hass.states.get(entity)

        if state is None:
            return None

        try:
            return float(state.state)
        except (ValueError, TypeError):
            _LOGGER.debug("%s: no numeric state", entity)
            return None
