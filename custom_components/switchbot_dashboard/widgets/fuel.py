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

    A fixed max_price ages badly: prices swing by tens of cents
    within a day and the level drifts over weeks. With
    ``max_price_entity`` the threshold follows a reference sensor
    instead - e.g. a statistics helper holding the lowest price of
    the last 7 days - plus ``price_margin``: "good" then means "at
    most 3 cents above the recent low". The fixed max_price stays as
    fallback while the reference has no value.

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
        max_price_entity: str = "",
        price_margin: float = 0.0,
        priority: int = 610,
    ):
        super().__init__(hass)

        self.level_entity = level_entity
        self.price_entity = price_entity
        self.min_level = min_level
        self.max_price = max_price
        self.max_price_entity = max_price_entity
        self.price_margin = price_margin
        self.unit = "%" if unit == "%" else "L"
        self.priority = priority

    def render(self):

        level = self._number(self.level_entity)
        price = self._number(self.price_entity)

        if level is None and price is None:
            return None

        level_low = level is not None and level <= self.min_level
        price_good = price is not None and price <= self._threshold()

        if level_low and price_good:
            value = f"{self.t('refuel')} {price:.2f}"
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

    def _threshold(self) -> float:
        """Price up to which refueling counts as a good deal."""

        if self.max_price_entity:
            reference = self._number(self.max_price_entity)

            if reference is not None:
                # rounded: 1.979 + 0.03 must compare equal to 2.009
                return round(reference + self.price_margin, 4)

        return self.max_price

    def _number(self, entity: str) -> float | None:

        state = self.hass.states.get(entity)

        if state is None:
            return None

        try:
            return float(state.state)
        except (ValueError, TypeError):
            _LOGGER.debug("%s: no numeric state", entity)
            return None
