from datetime import date
import logging

from .base import BaseWidget, DashboardItem
from ..config.entities import Entities
from ..icons import Icons

_LOGGER = logging.getLogger(__name__)

WASTE_TYPES = {
    "Restabfall": "Rest",
    "Gelber Sack": "Gelb",
    "Papier": "Papier",
    "Bioabfall": "Bio",
}


class WasteWidget(BaseWidget):

    def __init__(
        self,
        hass,
        entity: str = Entities.WASTE,
        days: int = 3,
        priority: int = 400,
    ):
        super().__init__(hass)
        self.entity = entity
        self.days = days
        self.priority = priority

    def render(self):

        state = self.hass.states.get(self.entity)

        if state is None:
            return None

        today = date.today()

        next_date = None
        waste_type = None

        for key, value in state.attributes.items():

            try:
                current = date.fromisoformat(key)
            except ValueError:
                continue

            if current < today:
                continue

            if next_date is None or current < next_date:
                next_date = current
                waste_type = value

        if next_date is None or waste_type is None:
            return None

        days = (next_date - today).days

        if days > self.days:
            return None

        parts = [
            WASTE_TYPES.get(item.strip(), item.strip())
            for item in waste_type.split(",")
        ]

        waste_text = "+".join(parts)

        if days == 0:
            value = f"{waste_text} {self.t('today')}"
            importance = 85
        elif days == 1:
            value = f"{waste_text} {self.t('tomorrow')}"
            importance = 75
        else:
            value = f"{waste_text} {days}{self.t('days')}"
            importance = 50

        _LOGGER.debug(
            "Next waste: %s (%s days) -> %s",
            next_date,
            days,
            waste_text,
        )

        return DashboardItem(
            icon=Icons.WASTE,
            value=value,
            priority=self.priority,
            importance=importance,
        )