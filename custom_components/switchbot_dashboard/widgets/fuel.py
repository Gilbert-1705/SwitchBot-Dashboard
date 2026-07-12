import logging

from .base import BaseWidget, DashboardItem
from ..icons import Icons

_LOGGER = logging.getLogger(__name__)


class FuelWidget(BaseWidget):
    """Tankfüllstand mit Tankempfehlung.

    Kombiniert Füllstand (Liter) und aktuellen Spritpreis (EUR/l)
    mit zwei Schwellenwerten:

        min_level  -> ab wann der Füllstand relevant wird
        max_price  -> bis zu welchem Preis sich Tanken lohnt

    Zustände:

        Füllstand niedrig UND Preis gut  -> "⛽ Tanken 1.65"  (wichtig)
        Füllstand niedrig                -> "⛽ 12L"
        Preis gut, Tank halb leer        -> "⛽ 1.65"          (Hinweis)
        sonst                            -> ausgeblendet
    """

    requires_config = True

    def __init__(
        self,
        hass,
        level_entity: str,
        price_entity: str,
        min_level: float = 15.0,
        max_price: float = 1.75,
        priority: int = 610,
    ):
        super().__init__(hass)

        self.level_entity = level_entity
        self.price_entity = price_entity
        self.min_level = min_level
        self.max_price = max_price
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
            value = f"{level:.0f}L"
            importance = 65

        elif price_good and level is not None and level <= self.min_level * 2:
            # Preis ist gut und der Tank ist nicht mehr voll -
            # günstige Gelegenheit, aber kein Muss
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
