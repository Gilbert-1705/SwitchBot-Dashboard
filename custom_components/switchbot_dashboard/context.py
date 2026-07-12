"""Day context: time windows that raise or lower importance.

The dashboard knows which part of the day it is — not through hard
modes but through importance modifiers. Waste matters in the
morning, windows and appliances in the evening:

    - type: waste
      entity: sensor.muell
      boost:
        - between: ["06:00", "09:00"]
          add: 20

Windows may wrap over midnight (["22:00", "06:00"]). Multiple
active windows add up. The boosted importance is clamped below the
alarm level: day context can make things louder, but only real
alarms (importance 100) trigger alarm mode.
"""

from datetime import datetime, time

from .const import IMPORTANCE_ALARM


def parse_time(value: str) -> time:
    hours, minutes = str(value).split(":")
    return time(int(hours), int(minutes))


def active_boost(boosts, now: time | None = None) -> int:
    """Sums the ``add`` values of all currently active windows."""

    if not boosts:
        return 0

    if now is None:
        now = datetime.now().time()

    total = 0

    for boost in boosts:

        start, end = (
            parse_time(boost["between"][0]),
            parse_time(boost["between"][1]),
        )

        if start <= end:
            active = start <= now < end
        else:
            # window wraps over midnight
            active = now >= start or now < end

        if active:
            total += int(boost["add"])

    return total


def apply_boost(importance: int, delta: int) -> int:
    """Applies a boost, clamped to 0..99.

    Alarm level (100) stays reserved for real alarms - a boost can
    never push an item into alarm mode, and an alarm is never
    softened below alarm level by a negative boost.
    """

    if importance >= IMPORTANCE_ALARM:
        return importance

    boosted = importance + delta

    return max(0, min(boosted, IMPORTANCE_ALARM - 1))
