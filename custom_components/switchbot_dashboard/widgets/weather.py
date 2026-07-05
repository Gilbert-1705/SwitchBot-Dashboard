from .entity import EntityWidget
from ..config.entities import Entities
from ..icons import Icons

TREND_ICONS = {
    "sunny": Icons.SUN,
    "cloudy": Icons.CLOUD,
    "rainy": Icons.RAIN,
}


class WeatherWidget(EntityWidget):

    requires_config = False

    def __init__(self, hass):
        super().__init__(
            hass=hass,
            entity=Entities.WEATHER_TEMPERATURE,
            icon=Icons.TEMP,
            priority=100,
        )

    def format_value(self, state):

        try:
            temperature = round(float(state.state))
        except (ValueError, TypeError):
            return "?"

        trend = self.hass.states.get(
            Entities.WEATHER_TREND
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