from .base import BaseWidget, DashboardItem
from ..icons import Icons
from ..text import join_names, state_text

# states that mean "everything is fine" (compared case-insensitively)
DEFAULT_OK_STATES = (
    "on", "home", "up", "online", "connected", "running", "ok",
    "true", "active", "healthy",
)

MISSING_STATES = ("unknown", "unavailable", "none")


class StatusWidget(BaseWidget):
    """Shows only what is down: servers, VPN, services, ...

        ! NAS           one entity is not ok
        ! NAS+VPN       two
        ! NAS+2         three or more
        (nothing)       everything is fine

    An entity that is unavailable counts as down by default - for a
    monitored server "no answer" is the failure.
    """

    def __init__(
        self,
        hass,
        entities: dict[str, str],
        icon: str = Icons.WARNING,
        ok_states: list | None = None,
        unavailable_is_problem: bool = True,
        importance: int = 85,
        priority: int = 60,
    ):
        super().__init__(hass)

        # entity_id -> display name
        self.entities = entities
        self.icon = icon
        self.ok_states = tuple(
            state_text(state).lower()
            for state in (ok_states or DEFAULT_OK_STATES)
        )
        self.unavailable_is_problem = unavailable_is_problem
        self.importance = importance
        self.priority = priority

    def render(self):

        problems = []

        for entity, name in self.entities.items():

            state = self.hass.states.get(entity)
            value = "none" if state is None else str(state.state).lower()

            if value in MISSING_STATES:
                if self.unavailable_is_problem:
                    problems.append(name)
                continue

            if value not in self.ok_states:
                problems.append(name)

        if not problems:
            return None

        return DashboardItem(
            icon=self.icon,
            value=join_names(problems),
            priority=self.priority,
            importance=self.importance,
        )
