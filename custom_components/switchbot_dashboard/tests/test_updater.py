"""Tests for the event-driven refresh (updater).

Run (from the repo root):

    python3 custom_components/switchbot_dashboard/tests/test_updater.py
"""

import asyncio
import unittest

import helpers  # noqa: F401  (stubs HA/aiohttp, sets sys.path)
from helpers import FakeHass, FakeState

from custom_components.switchbot_dashboard.updater import (
    DashboardUpdater,
    collect_entities,
)
from custom_components.switchbot_dashboard.widgets.config_models import (
    ApplianceWidgetConfig,
    EntityWidgetConfig,
    FuelWidgetConfig,
    WidgetConfig,
    WindowWidgetConfig,
)


class FakeAPI:

    def __init__(self):
        self.sent = []

    async def send_text(self, text):
        self.sent.append(text)


class CollectEntitiesTest(unittest.TestCase):

    def test_collects_all_entity_fields(self):

        entities = collect_entities([
            EntityWidgetConfig(type="entity", entity="sensor.power",
                               icon="P"),
            WindowWidgetConfig(type="window", entities={
                "binary_sensor.b1": "Balkon 1",
                "binary_sensor.b2": "Balkon 2",
            }),
            FuelWidgetConfig(type="fuel", level_entity="sensor.tank",
                             price_entity="sensor.preis"),
            ApplianceWidgetConfig(
                type="appliance", name="WM",
                running_entity="sensor.wm",
                done_entity="input_boolean.wm",
            ),
            WidgetConfig(type="waste"),
        ])

        self.assertEqual(entities, {
            "sensor.power",
            "binary_sensor.b1",
            "binary_sensor.b2",
            "sensor.tank",
            "sensor.preis",
            "sensor.wm",
            "input_boolean.wm",
        })

    def test_empty_configs(self):
        self.assertEqual(collect_entities(None), set())


class UpdaterTest(unittest.TestCase):

    def _updater(self, hass, api, min_interval=0):
        return DashboardUpdater(
            hass,
            api=api,
            configs=[
                EntityWidgetConfig(
                    type="entity", entity="s", icon="P",
                    formatter="power",
                ),
            ],
            max_items=5,
            min_interval=min_interval,
        )

    def test_sends_on_first_refresh(self):

        api = FakeAPI()
        hass = FakeHass({"s": FakeState("380")})
        updater = self._updater(hass, api)

        asyncio.run(updater.async_refresh())

        self.assertEqual(api.sent, ["P 380W"])

    def test_unchanged_content_is_not_resent(self):

        api = FakeAPI()
        hass = FakeHass({"s": FakeState("380")})
        updater = self._updater(hass, api)

        asyncio.run(updater.async_refresh())
        asyncio.run(updater.async_refresh())

        self.assertEqual(len(api.sent), 1)

    def test_changed_content_is_sent(self):

        api = FakeAPI()
        state = FakeState("380")
        hass = FakeHass({"s": state})
        updater = self._updater(hass, api)

        asyncio.run(updater.async_refresh())
        state.state = "500"
        asyncio.run(updater.async_refresh())

        self.assertEqual(api.sent, ["P 380W", "P 500W"])

    def test_force_resends_unchanged_content(self):

        api = FakeAPI()
        hass = FakeHass({"s": FakeState("380")})
        updater = self._updater(hass, api)

        asyncio.run(updater.async_refresh())
        asyncio.run(updater.async_refresh(force=True))

        self.assertEqual(len(api.sent), 2)

    def test_rate_limit_defers_send(self):

        api = FakeAPI()
        state = FakeState("380")
        hass = FakeHass({"s": state})
        updater = self._updater(hass, api, min_interval=60)

        asyncio.run(updater.async_refresh())

        # The value changes right after: the rate limit kicks in,
        # a retry is scheduled instead of sending
        state.state = "500"
        asyncio.run(updater.async_refresh())

        self.assertEqual(api.sent, ["P 380W"])
        self.assertGreater(updater.seconds_until_allowed(), 0)
        self.assertIsNotNone(updater._cancel_retry)

    def test_force_bypasses_rate_limit(self):

        api = FakeAPI()
        state = FakeState("380")
        hass = FakeHass({"s": state})
        updater = self._updater(hass, api, min_interval=60)

        asyncio.run(updater.async_refresh())
        state.state = "500"
        asyncio.run(updater.async_refresh(force=True))

        self.assertEqual(api.sent, ["P 380W", "P 500W"])


class PreviewEntityTest(unittest.TestCase):
    """Local preview entity sensor.switchbot_dashboard."""

    PREVIEW = "sensor.switchbot_dashboard"

    def _updater(self, hass, api, dry_run=False):
        return DashboardUpdater(
            hass,
            api=api,
            configs=[
                EntityWidgetConfig(
                    type="entity", entity="s", icon="P",
                    formatter="power",
                ),
            ],
            max_items=5,
            min_interval=0,
            dry_run=dry_run,
        )

    def test_preview_entity_mirrors_display(self):

        api = FakeAPI()
        hass = FakeHass({"s": FakeState("380")})

        asyncio.run(self._updater(hass, api).async_refresh())

        state, attrs = hass.set_states[self.PREVIEW]
        self.assertEqual(state, "P 380W")
        self.assertTrue(attrs["sent_to_device"])

    def test_preview_updates_even_when_send_skipped(self):

        api = FakeAPI()
        hass = FakeHass({"s": FakeState("380")})
        updater = self._updater(hass, api)

        asyncio.run(updater.async_refresh())
        hass.set_states.clear()
        asyncio.run(updater.async_refresh())  # unchanged -> no send

        state, attrs = hass.set_states[self.PREVIEW]
        self.assertEqual(state, "P 380W")
        self.assertFalse(attrs["sent_to_device"])

    def test_dry_run_never_calls_api(self):

        api = FakeAPI()
        state = FakeState("380")
        hass = FakeHass({"s": state})
        updater = self._updater(hass, api, dry_run=True)

        asyncio.run(updater.async_refresh())
        state.state = "500"
        asyncio.run(updater.async_refresh(force=True))

        self.assertEqual(api.sent, [])
        preview_state, attrs = hass.set_states[self.PREVIEW]
        self.assertEqual(preview_state, "P 500W")
        self.assertFalse(attrs["sent_to_device"])


if __name__ == "__main__":
    unittest.main()
