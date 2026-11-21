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
        self.raw = []

    async def send_text(self, text):
        # raw: exactly what goes to the device (no-break spaces inside
        # items); sent: as readable text for the assertions
        self.raw.append(text)
        self.sent.append(text.replace("\u00a0", " "))


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


class EventLoopSafetyTest(unittest.TestCase):
    """Home Assistant threading rules that the stubs cannot enforce.

    HA runs a plain (non-coroutine) listener in a worker thread
    unless it is decorated with @callback. The state listener
    schedules a timer, which is only allowed on the event loop.
    """

    def test_state_listener_is_declared_as_callback(self):
        import inspect

        source = inspect.getsource(DashboardUpdater)
        index = source.index("def _on_state_change")
        preceding = source[:index].rstrip().splitlines()[-1].strip()

        self.assertEqual(preceding, "@callback")

    def test_pending_debounce_timer_is_not_restarted(self):
        # A sensor that reports more often than the debounce time
        # must not postpone the refresh forever
        from custom_components.switchbot_dashboard import updater as mod

        calls = []
        original = mod.async_call_later
        mod.async_call_later = (
            lambda hass, delay, action: calls.append(delay) or (lambda: None)
        )
        try:
            updater = DashboardUpdater(
                FakeHass({}), api=FakeAPI(), configs=[], max_items=5
            )
            for _ in range(10):
                updater._on_state_change(None)
        finally:
            mod.async_call_later = original

        self.assertEqual(len(calls), 1)

    def test_timer_targets_are_coroutines(self):
        import inspect

        for name in ("_on_debounce_done", "_on_interval", "_on_retry",
                     "_on_started"):
            self.assertTrue(
                inspect.iscoroutinefunction(getattr(DashboardUpdater, name)),
                name,
            )


class FreshHostTest(unittest.TestCase):
    """The first send must not wait for the rate limit.

    time.monotonic() counts from boot. On a host (or CI runner) that
    started a few seconds ago, a "last send" of 0.0 looked like a
    send moments ago and held back the first dashboard.
    """

    def test_first_send_right_after_boot(self):
        import custom_components.switchbot_dashboard.updater as module

        original = module.time.monotonic
        module.time.monotonic = lambda: 5.0
        try:
            api = FakeAPI()
            updater = DashboardUpdater(
                FakeHass({"s": FakeState("380")}),
                api=api,
                configs=[
                    EntityWidgetConfig(
                        type="entity", entity="s", icon="P",
                        formatter="power",
                    ),
                ],
                max_items=5,
            )
            self.assertEqual(updater.seconds_until_allowed(), 0)
            asyncio.run(updater.async_refresh())
        finally:
            module.time.monotonic = original

        self.assertEqual(api.sent, ["P 380W"])


class KeepItemsTogetherTest(unittest.TestCase):
    """The device may only wrap between items, never inside one."""

    def test_text_helper(self):
        from custom_components.switchbot_dashboard.text import (
            NBSP, keep_items_together,
        )

        sent = keep_items_together(
            "🌡 2°C ☀   🧺 TR Fertig   ⛽ Tanken 1.98", "   "
        )
        self.assertEqual(
            sent,
            f"🌡{NBSP}2°C{NBSP}☀   🧺{NBSP}TR{NBSP}Fertig   "
            f"⛽{NBSP}Tanken{NBSP}1.98",
        )
        # only the separators remain breakable
        self.assertEqual(sent.count(" "), 6)

    def test_single_item_and_empty_text(self):
        from custom_components.switchbot_dashboard.text import (
            NBSP, keep_items_together,
        )

        self.assertEqual(keep_items_together("● ", "   "), f"●{NBSP}")
        self.assertEqual(keep_items_together("", "   "), "")

    def test_updater_sends_protected_text_preview_stays_plain(self):
        from custom_components.switchbot_dashboard.text import NBSP

        api = FakeAPI()
        hass = FakeHass({"s": FakeState("380")})
        updater = DashboardUpdater(
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
        )
        asyncio.run(updater.async_refresh())

        self.assertEqual(api.raw, [f"P{NBSP}380W"])
        state, _ = hass.set_states["sensor.switchbot_dashboard"]
        self.assertEqual(state, "P 380W")


class FailingAPI:
    """Refuses the first ``failures`` sends like a rate-limited API."""

    def __init__(self, failures=1, status=429):
        self.failures = failures
        self.status = status
        self.attempts = []

    async def send_text(self, text):
        self.attempts.append(text.replace("\u00a0", " "))

        if len(self.attempts) <= self.failures:
            return {"statusCode": self.status, "message": "HTTP 429"}

        return {"statusCode": 100, "message": "success"}


class SendFailureTest(unittest.TestCase):
    """A refused send must not count as 'display is up to date'."""

    def _updater(self, hass, api):
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
        )

    def test_rate_limited_send_is_retried(self):

        api = FailingAPI(failures=1)
        hass = FakeHass({"s": FakeState("380")})
        updater = self._updater(hass, api)

        asyncio.run(updater.async_refresh())

        # refused: a retry is scheduled and the text is forgotten
        self.assertIsNotNone(updater._cancel_retry)
        self.assertIsNone(updater._last_text)

        # the unchanged text is sent again on the next refresh
        asyncio.run(updater.async_refresh())

        self.assertEqual(api.attempts, ["P 380W", "P 380W"])
        self.assertEqual(updater._last_text, "P 380W")

    def test_preview_reports_not_sent_after_failure(self):

        api = FailingAPI(failures=1)
        hass = FakeHass({"s": FakeState("380")})

        asyncio.run(self._updater(hass, api).async_refresh())

        state, attrs = hass.set_states["sensor.switchbot_dashboard"]
        self.assertEqual(state, "P 380W")
        self.assertFalse(attrs["sent_to_device"])

    def test_successful_send_schedules_no_retry(self):

        api = FailingAPI(failures=0)
        hass = FakeHass({"s": FakeState("380")})
        updater = self._updater(hass, api)

        asyncio.run(updater.async_refresh())

        self.assertIsNone(updater._cancel_retry)
        self.assertEqual(updater._last_text, "P 380W")


class FakeResponse:

    def __init__(self, status, body=None, error=None):
        self.status = status
        self._body = body
        self._error = error

    async def json(self, content_type=None):
        if self._error is not None:
            raise self._error
        return self._body


class ReadResultTest(unittest.TestCase):
    """The API answer must never raise, whatever its format."""

    def _read(self, response):
        from custom_components.switchbot_dashboard.api import SwitchBotAPI

        return asyncio.run(SwitchBotAPI._read_result(response))

    def test_success_body_is_passed_through(self):
        result = self._read(
            FakeResponse(200, {"statusCode": 100, "message": "success"})
        )
        self.assertEqual(result["statusCode"], 100)

    def test_http_429_without_json_body(self):
        # exactly what SwitchBot sends when rate limited: reading the
        # body as JSON would raise aiohttp's ContentTypeError
        result = self._read(
            FakeResponse(429, error=AssertionError("must not be read"))
        )
        self.assertEqual(result["statusCode"], 429)

    def test_invalid_json_body(self):
        result = self._read(FakeResponse(200, error=ValueError("bad")))
        self.assertEqual(result["message"], "invalid response body")

    def test_non_dict_body(self):
        result = self._read(FakeResponse(200, ["unexpected"]))
        self.assertEqual(result["message"], "unexpected response body")


class FakeSession:
    """Stands in for aiohttp.ClientSession; ``post`` fails with ``error``."""

    instances = []

    def __init__(self, error=None, response=None, **kwargs):
        self.error = error
        self.response = response
        self.kwargs = kwargs
        FakeSession.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def post(self, *args, **kwargs):
        session = self

        class _Request:
            async def __aenter__(self):
                if session.error is not None:
                    raise session.error
                return session.response

            async def __aexit__(self, *exc):
                return False

        return _Request()


class NetworkFailureTest(unittest.TestCase):
    """A dropped or hanging connection is a failed send, not a crash."""

    def setUp(self):
        from custom_components.switchbot_dashboard import api as api_module

        self.api_module = api_module
        self._original = api_module.ClientSession
        FakeSession.instances = []

    def tearDown(self):
        self.api_module.ClientSession = self._original

    def _send(self, error=None, response=None):
        self.api_module.ClientSession = (
            lambda **kwargs: FakeSession(error, response, **kwargs)
        )
        api = self.api_module.SwitchBotAPI("token", "secret", "device")
        return asyncio.run(api.send_text("P 380W"))

    def test_connection_error_becomes_a_failed_result(self):
        import aiohttp
        from custom_components.switchbot_dashboard.updater import (
            send_succeeded,
        )

        with self.assertLogs(
            "custom_components.switchbot_dashboard.api", "WARNING"
        ):
            result = self._send(aiohttp.ClientError("Cannot connect"))

        self.assertEqual(result["statusCode"], self.api_module.NETWORK_ERROR)
        self.assertIn("Cannot connect", result["message"])
        self.assertFalse(send_succeeded(result))

    def test_timeout_becomes_a_failed_result(self):
        with self.assertLogs(
            "custom_components.switchbot_dashboard.api", "WARNING"
        ):
            result = self._send(asyncio.TimeoutError())

        self.assertEqual(result["statusCode"], self.api_module.NETWORK_ERROR)
        self.assertEqual(result["message"], "TimeoutError")

    def test_request_has_a_timeout(self):
        self._send(
            response=FakeResponse(200, {"statusCode": 100})
        )

        timeout = FakeSession.instances[0].kwargs["timeout"]
        self.assertEqual(timeout.total, self.api_module.REQUEST_TIMEOUT)

    def test_successful_send_is_unchanged(self):
        result = self._send(
            response=FakeResponse(200, {"statusCode": 100})
        )
        self.assertEqual(result["statusCode"], 100)

    def test_updater_retries_after_a_network_failure(self):
        import aiohttp

        self.api_module.ClientSession = (
            lambda **kwargs: FakeSession(
                aiohttp.ClientError("Network is unreachable"), **kwargs
            )
        )
        api = self.api_module.SwitchBotAPI("token", "secret", "device")
        hass = FakeHass({"s": FakeState("380")})
        updater = DashboardUpdater(
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
        )

        with self.assertLogs(
            "custom_components.switchbot_dashboard.api", "WARNING"
        ):
            asyncio.run(updater.async_refresh())

        # not remembered as sent, a retry is scheduled, preview honest
        self.assertIsNone(updater._last_text)
        self.assertIsNotNone(updater._cancel_retry)
        state, attrs = hass.set_states["sensor.switchbot_dashboard"]
        self.assertFalse(attrs["sent_to_device"])


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

    def test_unchanged_render_does_not_rewrite_the_entity(self):
        # Found in production: any watched entity triggers a render
        # every few seconds. Rewriting the preview entity each time
        # flooded the recorder with identical rows.
        api = FakeAPI()
        hass = FakeHass({"s": FakeState("380")})
        updater = self._updater(hass, api)

        asyncio.run(updater.async_refresh())
        hass.set_states.clear()

        for _ in range(5):
            asyncio.run(updater.async_refresh())  # unchanged

        self.assertEqual(hass.set_states, {})
        self.assertEqual(len(api.sent), 1)

    def test_entity_is_rewritten_when_the_text_changes(self):

        api = FakeAPI()
        state = FakeState("380")
        hass = FakeHass({"s": state})
        updater = self._updater(hass, api)

        asyncio.run(updater.async_refresh())
        hass.set_states.clear()
        state.state = "500"
        asyncio.run(updater.async_refresh())

        preview_state, attrs = hass.set_states[self.PREVIEW]
        self.assertEqual(preview_state, "P 500W")
        self.assertTrue(attrs["sent_to_device"])

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
