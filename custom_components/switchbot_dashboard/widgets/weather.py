from .entity import EntityWidget
from ..config.entities import Entities
from ..icons import Icons

TREND_ICONS = {
    "sunny": Icons.SUN,
    "cloudy": Icons.CLOUD,
    "rainy": Icons.RAIN,
}


class WeatherWidget(EntityWidget):

    def __init__(
        self,
        hass,
        temperature_entity: str = Entities.WEATHER_TEMPERATURE,
        trend_entity: str = Entities.WEATHER_TREND,
        icon: str = Icons.TEMP,
        priority: int = 100,
        # Wetter gehört immer aufs Dashboard
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

    def format_value(self, state):

        try:
            temperature = round(float(state.state))
        except (ValueError, TypeError):
            return "?"

        trend = self.hass.states.get(
            self.trend_entity
        )

        icon = ""

        if trend:
            icon = TREND_ICONS.get(
                trend.state,
                "",
            )

        if icon:
            return f"{temperature}°C {icon}"

        return f"{temperature}°C"