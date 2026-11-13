"""Remembers since when an entity has been in its current state.

Reminders grow louder over time ("laundry waiting for 3 hours") and
alerts can require a duration ("door open for 10 minutes"). Home
Assistant's ``last_changed`` is no reliable clock for that: it is
re-stamped on every restart, so a waiting reminder would start over
at its lowest level.

The tracker keeps its own record per entity - the state it last saw
and when that state began - and persists it. After a restart the
entity comes back in the same state and the original start time
still applies.

Widgets report an entity on EVERY render, whatever its state. That
way the record follows each transition (on -> off -> on) and an old
start time is never reused for a new period.
"""

from datetime import datetime, timezone

from .const import DOMAIN

SAVE_DELAY_SECONDS = 10
TRACKER_KEY = "tracker"


class SinceTracker:

    def __init__(self, store=None):
        # store: homeassistant.helpers.storage.Store or None (tests)
        self._store = store
        self._data: dict[str, dict] = {}

    async def async_load(self):

        if self._store is None:
            return

        data = await self._store.async_load()

        if isinstance(data, dict):
            self._data = data

    def since(self, entity_id: str, state: str, last_changed=None):
        """Returns when ``entity_id`` entered ``state``.

        Call it on every render. A state different from the recorded
        one starts a new period at ``last_changed`` (or now).
        """

        record = self._data.get(entity_id)

        if record is not None and record.get("state") == state:
            stored = self._parse(record.get("since"))

            if stored is not None:
                # After a restart last_changed is later than the real
                # start; the earlier of the two is the truth.
                if last_changed is not None and last_changed < stored:
                    return last_changed
                return stored

        started = last_changed or datetime.now(timezone.utc)

        self._data[entity_id] = {
            "state": state,
            "since": started.isoformat(),
        }
        self._schedule_save()

        return started

    def _schedule_save(self):

        if self._store is not None:
            self._store.async_delay_save(
                lambda: self._data, SAVE_DELAY_SECONDS
            )

    @staticmethod
    def _parse(value):

        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return None


def state_since(hass, entity_id: str, state):
    """Start of the entity's current state, restart-proof if possible.

    Uses the tracker when the integration has set one up and falls
    back to ``last_changed`` otherwise (e.g. in tests).
    """

    if state is None:
        return None

    last_changed = getattr(state, "last_changed", None)

    data = getattr(hass, "data", None)
    tracker = None

    if isinstance(data, dict):
        tracker = data.get(DOMAIN, {}).get(TRACKER_KEY)

    if tracker is None:
        return last_changed

    return tracker.since(entity_id, str(state.state), last_changed)
