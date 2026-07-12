"""Event-driven dashboard refresh.

Watches all configured entities and updates the display
automatically. Three safeguards keep the API and the e-paper calm:

1. Debounce: state changes are collected for 5 s before rendering
   (door contacts flap, spin cycles pause, ...).
2. Change detection: only send when the rendered line actually
   changed.
3. Rate limit: at most one API call per minute (SwitchBot
   recommendation); earlier triggers are deferred to the next
   allowed moment.

A periodic refresh (default: 15 min) catches changes without a
state event, e.g. the date rollover for waste and calendar widgets.
"""

import logging
import time
from dataclasses import fields as dataclass_fields
from datetime import timedelta

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)

from .render import publish_preview, render_dashboard

_LOGGER = logging.getLogger(__name__)

DEBOUNCE_SECONDS = 5
MIN_SEND_INTERVAL = 60
PERIODIC_REFRESH = 900


def collect_entities(configs) -> set[str]:
    """Collects all entity IDs from the widget configurations.

    Convention: fields named ``entity`` or ending in ``_entity``,
    plus the keys of ``entities`` mappings.
    """

    entities: set[str] = set()

    for cfg in configs or ():

        for field in dataclass_fields(cfg):

            value = getattr(cfg, field.name)

            if not value:
                continue

            if field.name == "entity" or field.name.endswith("_entity"):
                entities.add(value)

            elif field.name == "entities" and isinstance(value, dict):
                entities.update(value)

    return entities


class DashboardUpdater:

    def __init__(
        self,
        hass,
        api,
        configs,
        max_items: int,
        debounce: float = DEBOUNCE_SECONDS,
        min_interval: float = MIN_SEND_INTERVAL,
        interval: float = PERIODIC_REFRESH,
        dry_run: bool = False,
    ):
        self.hass = hass
        self.api = api
        self.configs = configs
        self.max_items = max_items
        self.debounce = debounce
        self.min_interval = min_interval
        self.interval = interval
        # dry_run: only update the local preview entity, never
        # call the SwitchBot API (development)
        self.dry_run = dry_run

        self._last_text: str | None = None
        self._last_send: float = 0.0
        self._cancel_debounce = None
        self._cancel_retry = None
        self._unsubs = []

    # -- Lifecycle ------------------------------------------------

    async def async_start(self):

        entities = sorted(collect_entities(self.configs))

        if entities:
            self._unsubs.append(
                async_track_state_change_event(
                    self.hass, entities, self._on_state_change
                )
            )
            _LOGGER.debug("Watching %d entities", len(entities))

        self._unsubs.append(
            async_track_time_interval(
                self.hass,
                self._on_interval,
                timedelta(seconds=self.interval),
            )
        )

        # Initial render - wait until HA has fully started so
        # all entities are available
        if self.hass.is_running:
            await self.async_refresh()
        else:
            self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED, self._on_started
            )

    async def _on_started(self, _event):
        await self.async_refresh()

    def async_stop(self):

        for unsub in self._unsubs:
            unsub()

        self._unsubs.clear()
        self._cancel_timers()

    # -- Trigger --------------------------------------------------

    def _on_state_change(self, event):

        if self._cancel_debounce is not None:
            self._cancel_debounce()

        self._cancel_debounce = async_call_later(
            self.hass, self.debounce, self._on_debounce_done
        )

    async def _on_debounce_done(self, _now):
        self._cancel_debounce = None
        await self.async_refresh()

    async def _on_interval(self, _now):
        await self.async_refresh()

    # -- Refresh --------------------------------------------------

    def should_send(self, text: str, force: bool = False) -> bool:
        """Only send when the display content changed."""

        if force:
            return True

        return text != self._last_text

    def seconds_until_allowed(self) -> float:
        """Remaining rate-limit wait time (0 = allowed now)."""

        elapsed = time.monotonic() - self._last_send

        return max(0.0, self.min_interval - elapsed)

    async def async_refresh(self, force: bool = False):

        text = render_dashboard(
            self.hass, self.configs, self.max_items
        )

        if not self.should_send(text, force=force):
            _LOGGER.debug("Dashboard unchanged, skipping send")
            publish_preview(self.hass, text, sent=False)
            return

        wait = self.seconds_until_allowed()

        if wait > 0 and not force:
            publish_preview(self.hass, text, sent=False)
            self._schedule_retry(wait)
            return

        self._cancel_timers()
        self._last_text = text
        self._last_send = time.monotonic()

        publish_preview(self.hass, text, sent=not self.dry_run)

        if self.dry_run:
            _LOGGER.debug("Dry run, not sending: %s", text)
            return

        _LOGGER.debug("Sending dashboard: %s", text)
        await self.api.send_text(text)

    def _schedule_retry(self, wait: float):

        if self._cancel_retry is not None:
            return  # already scheduled

        _LOGGER.debug("Rate limit: retry in %.0fs", wait)

        self._cancel_retry = async_call_later(
            self.hass, wait, self._on_retry
        )

    async def _on_retry(self, _now):
        self._cancel_retry = None
        await self.async_refresh()

    def _cancel_timers(self):

        if self._cancel_debounce is not None:
            self._cancel_debounce()
            self._cancel_debounce = None

        if self._cancel_retry is not None:
            self._cancel_retry()
            self._cancel_retry = None
