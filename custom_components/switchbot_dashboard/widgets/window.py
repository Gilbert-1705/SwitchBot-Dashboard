from .base import BaseWidget, DashboardItem


class WindowWidget(BaseWidget):

    requires_config = True

    def __init__(
        self,
        hass,
        entities: list[str],
        priority: int = 250,
    ):
        super().__init__(hass)

        self.entities = entities
        self.priority = priority

    def render(self):

        open_windows = 0

        for entity in self.entities:

            state = self.hass.states.get(entity)

            if state is None:
                continue

            if state.state in (
                "on",
                "open",
                "true",
            ):
                open_windows += 1

        if open_windows == 0:
            value = "●"
        else:
            value = f"○{open_windows}"

        return DashboardItem(
            icon="",
            value=value,
            priority=self.priority,
        )