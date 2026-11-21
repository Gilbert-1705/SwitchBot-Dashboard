import logging

from .entity import EntityWidget
from ..config.entities import Entities
from ..const import DOMAIN
from ..icons import Icons

_LOGGER = logging.getLogger(__name__)

TREND_ICONS = {
    "sunny": Icons.SUN,
    "cloudy": Icons.CLOUD,
    "rainy": Icons.RAIN,
}

# hass.data keys: last shown temperature per sensor (hysteresis) and
# sensors currently replaced by their reference
SHOWN_KEY = "weather_shown"
FALLBACK_KEY = "weather_fallback"

# back to the local sensor only once it is this much closer than
# max_deviation - otherwise a sensor hovering at the limit flips
# between local and reference value (seen live: 6 °C -> 2 °C -> 6 °C)
FALLBACK_MARGIN = 1.0


class WeatherWidget(EntityWidget):
    """Temperature + trend: ``🌡 21°C ☀``.

    Two optional calming measures:

    hysteresis
        The shown degree only changes once the measurement has moved
        at least this far away from it. A sensor hovering around
        3.5 °C no longer flips between 3 and 4 - and every flip is
        an e-ink refresh.

    reference_entity / max_deviation
        A second sensor (e.g. a weather service) as plausibility
        check. If the local sensor is off by more than
        ``max_deviation`` - typically because the sun is shining on
        it - or unavailable, the reference value is shown instead.
    """

    def __init__(
        self,
        hass,
        temperature_entity: str = Entities.WEATHER_TEMPERATURE,
        trend_entity: str = Entities.WEATHER_TREND,
        icon: str = Icons.TEMP,
        reference_entity: str = "",
        max_deviation: float = 4.0,
        hysteresis: float = 0.75,
        priority: int = 100,
        # Weather always belongs on the dashboard
        importance: int = 90,
    ):
        super().__init__(
            hass=hass,
            entity=temperature_entity,
            icon=icon,
            priority=priority,
            importance=importance,
        )
        self.trend_entity = trend_entity
        self.reference_entity = reference_entity
        self.max_deviation = max_deviation
        self.hysteresis = hysteresis

    # -- measurement ----------------------------------------------

    def _read(self, entity_id: str) -> float | None:

        if not entity_id:
            return None

        state = self.hass.states.get(entity_id)

        try:
            return float(state.state)
        except (AttributeError, ValueError, TypeError):
            return None

    def measured(self) -> float | None:
        """Local value, or the reference when the local one is off."""

        local = self._read(self.entity)
        reference = self._read(self.reference_entity)

        if local is None:
            return reference

        if reference is None:
            return local

        fallback = self.hass.data.setdefault(DOMAIN, {}).setdefault(
            FALLBACK_KEY, set()
        )
        deviation = abs(local - reference)

        if self.entity in fallback:
            limit = self.max_deviation - FALLBACK_MARGIN
        else:
            limit = self.max_deviation

        if deviation > limit:
            if self.entity not in fallback:
                _LOGGER.debug(
                    "%s deviates from %s (%.1f vs %.1f), using the "
                    "reference",
                    self.entity, self.reference_entity, local, reference,
                )
            fallback.add(self.entity)
            return reference

        fallback.discard(self.entity)
        return local

    def shown(self, value: float) -> int:
        """Rounded value with hysteresis against flickering."""

        memory = self.hass.data.setdefault(DOMAIN, {}).setdefault(
            SHOWN_KEY, {}
        )
        previous = memory.get(self.entity)

        if (
            previous is not None
            and self.hysteresis > 0
            and abs(value - previous) < self.hysteresis
        ):
            return previous

        shown = round(value)
        memory[self.entity] = shown

        return shown

    # -- rendering --------------------------------------------------

    def available(self) -> bool:
        return self.measured() is not None

    def format_value(self, state):

        value = self.measured()

        if value is None:
            return "?"

        temperature = self.shown(value)

        trend = self.hass.states.get(self.trend_entity)
        icon = TREND_ICONS.get(trend.state, "") if trend else ""

        if icon:
            return f"{temperature}°C {icon}"

        return f"{temperature}°C"
