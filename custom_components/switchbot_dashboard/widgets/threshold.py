from .base import BaseWidget, DashboardItem


class ThresholdWidget(BaseWidget):
    """Shows a numeric sensor only while it is out of bounds.

    One widget for everything that is "fine until it isn't" - or
    worth knowing only when it is good:

        air quality   CO2 above 1000 ppm        -> "CO₂ 1450"
        electricity   price below 20 ct         -> "€ 18ct"
        humidity      below 35 % or above 65 %  -> "💧 71%"

    ``above`` / ``below`` are the bounds that make the value worth
    showing; ``critical_above`` / ``critical_below`` raise it to the
    always-shown band. Inside the bounds the widget is hidden.
    """

    def __init__(
        self,
        hass,
        entity: str,
        icon: str,
        name: str = "",
        above: float | None = None,
        below: float | None = None,
        critical_above: float | None = None,
        critical_below: float | None = None,
        unit: str = "",
        precision: int = 0,
        importance: int = 55,
        priority: int = 800,
    ):
        super().__init__(hass)

        self.entity = entity
        self.icon = icon
        self.name = name
        self.above = above
        self.below = below
        self.critical_above = critical_above
        self.critical_below = critical_below
        self.unit = unit
        self.precision = precision
        self.importance = importance
        self.priority = priority

    def render(self):

        state = self.hass.states.get(self.entity)

        if state is None:
            return None

        try:
            value = float(state.state)
        except (ValueError, TypeError):
            return None

        if self._beyond(value, self.critical_above, self.critical_below):
            importance = 85
        elif self._beyond(value, self.above, self.below):
            importance = self.importance
        else:
            return None

        text = f"{value:.{self.precision}f}{self.unit}"

        return DashboardItem(
            icon=self.icon,
            value=f"{self.name} {text}".strip(),
            priority=self.priority,
            importance=importance,
        )

    @staticmethod
    def _beyond(value, above, below) -> bool:

        if above is not None and value > above:
            return True

        if below is not None and value < below:
            return True

        return False
