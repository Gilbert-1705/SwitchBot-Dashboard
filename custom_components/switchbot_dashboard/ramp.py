"""Time-based importance: information gets more urgent over time.

A finished washing machine is a side note after five minutes but
demands attention after three hours. Widgets use the state's
``last_changed`` timestamp (provided by Home Assistant for free),
so no extra bookkeeping is needed.

Note: the periodic refresh of the updater (every 15 minutes)
re-renders the dashboard, so ramped importance takes effect even
without a state change.
"""

from datetime import datetime, timezone

# (seconds since last_changed, importance) - ascending
Steps = tuple[tuple[float, int], ...]


def time_based_importance(
    last_changed,
    steps: Steps,
    now: datetime | None = None,
) -> int:
    """Returns the importance for the elapsed time since last_changed.

    ``steps`` is an ascending sequence like
    ``((0, 30), (3600, 60), (10800, 100))``: importance 30 right
    away, 60 after an hour, 100 after three hours. Without a
    timestamp the first step applies.
    """

    if not steps:
        return 0

    if last_changed is None:
        return steps[0][1]

    if now is None:
        now = datetime.now(timezone.utc)

    elapsed = (now - last_changed).total_seconds()

    result = steps[0][1]

    for threshold, importance in steps:
        if elapsed >= threshold:
            result = importance

    return result
