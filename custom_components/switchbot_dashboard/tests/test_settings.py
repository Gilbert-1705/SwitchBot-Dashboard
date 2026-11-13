"""Tests for settings, start-up and reloading without a restart.

Run (from the repo root):

    python3 custom_components/switchbot_dashboard/tests/test_settings.py
"""

import asyncio
import types
import unittest

import helpers  # noqa: F401  (stubs HA/aiohttp, sets sys.path)
from helpers import FakeHass, FakeState

import custom_components.switchbot_dashboard as integration
from custom_components.switchbot_dashboard.config.schema import ConfigError
from custom_components.switchbot_dashboard.const import DOMAIN
from custom_components.switchbot_dashboard.settings import (
    Settings,
    credentials_from,
    settings_from_yaml,
    with_options,
)

CREDENTIALS = {"token": "t", "secret": "s", "device_id": "d"}

WIDGETS = [
    {"type": "entity", "entity": "s", "icon": "P", "formatter": "power"},
]


class SettingsFromYamlTest(unittest.TestCase):

    def test_defaults(self):
        settings = settings_from_yaml(dict(CREDENTIALS))
        self.assertIsNone(settings.widgets)
        self.assertEqual(settings.max_items, 5)
        self.assertEqual(settings.quiet_max_items, 3)
        self.assertTrue(settings.auto_refresh)
        self.assertFalse(settings.dry_run)
        self.assertEqual(settings.language, "de")

    def test_all_options(self):
        settings = settings_from_yaml({
            **CREDENTIALS,
            "max_items": 4,
            "quiet_max_items": 2,
            "auto_refresh": False,
            "dry_run": True,
            "language": "en",
            "widgets": WIDGETS,
        })
        self.assertEqual(settings.max_items, 4)
        self.assertEqual(settings.quiet_max_items, 2)
        self.assertFalse(settings.auto_refresh)
        self.assertTrue(settings.dry_run)
        self.assertEqual(settings.language, "en")
        self.assertEqual(len(settings.widgets), 1)

    def test_widgets_only_block_is_valid(self):
        # credentials then come from a config entry (UI setup)
        settings = settings_from_yaml({"widgets": WIDGETS})
        self.assertEqual(len(settings.widgets), 1)

    def test_unknown_option_lists_available(self):
        with self.assertRaises(ConfigError) as ctx:
            settings_from_yaml({**CREDENTIALS, "max_item": 4})
        self.assertIn("unknown option 'max_item'", str(ctx.exception))
        self.assertIn("max_items", str(ctx.exception))

    def test_invalid_widget_is_reported(self):
        with self.assertRaises(ConfigError) as ctx:
            settings_from_yaml({**CREDENTIALS, "widgets": [{"type": "x"}]})
        self.assertIn("unknown type 'x'", str(ctx.exception))

    def test_invalid_values(self):
        cases = {
            "max_items": [0, 11, "viele", True],
            "quiet_max_items": [0, 99],
            "auto_refresh": ["ja", 1],
            "dry_run": ["nein"],
            "language": ["fr", ""],
        }
        for key, values in cases.items():
            for value in values:
                with self.assertRaises(ConfigError, msg=f"{key}={value!r}"):
                    settings_from_yaml({**CREDENTIALS, key: value})


class CredentialsTest(unittest.TestCase):

    def test_complete(self):
        self.assertEqual(credentials_from(CREDENTIALS), ("t", "s", "d"))

    def test_absent_means_config_entry(self):
        self.assertIsNone(credentials_from({"widgets": []}))

    def test_incomplete_is_an_error(self):
        with self.assertRaises(ConfigError) as ctx:
            credentials_from({"token": "t"})
        self.assertIn("secret", str(ctx.exception))
        self.assertIn("device_id", str(ctx.exception))


class WithOptionsTest(unittest.TestCase):

    def test_options_override_yaml(self):
        yaml_settings = settings_from_yaml({**CREDENTIALS, "max_items": 4})
        merged = with_options(yaml_settings, {"max_items": 2})
        self.assertEqual(merged.max_items, 2)
        # the original is untouched
        self.assertEqual(yaml_settings.max_items, 4)

    def test_unrelated_keys_are_ignored(self):
        merged = with_options(Settings(), {"token": "x", "widgets": 1})
        self.assertEqual(merged, Settings())

    def test_no_options(self):
        self.assertEqual(with_options(Settings(), None), Settings())
        self.assertEqual(with_options(Settings(), {}), Settings())

    def test_invalid_option_is_rejected(self):
        with self.assertRaises(ConfigError):
            with_options(Settings(), {"language": "xx"})


# ---------------------------------------------------------------------
# start-up and reload against a fake Home Assistant
# ---------------------------------------------------------------------

class RecordingAPI:
    """Replaces SwitchBotAPI: records what would be sent."""

    sent: list = []

    def __init__(self, token, secret, device_id):
        self.token = token

    async def send_text(self, text):
        RecordingAPI.sent.append(text)
        return {"statusCode": 100}


class RunningHass(FakeHass):
    """FakeHass with what start-up and services need."""

    def __init__(self, states=None):
        super().__init__(states)
        self.is_running = True
        self.registered = {}
        self.services = types.SimpleNamespace(
            async_register=lambda domain, name, handler:
                self.registered.__setitem__(name, handler)
        )
        self.bus = types.SimpleNamespace(
            async_listen_once=lambda event, action: None
        )


class StartAndReloadTest(unittest.TestCase):

    def setUp(self):
        RecordingAPI.sent = []
        self._api = integration.SwitchBotAPI
        self._yaml = integration.async_integration_yaml_config
        integration.SwitchBotAPI = RecordingAPI

    def tearDown(self):
        integration.SwitchBotAPI = self._api
        integration.async_integration_yaml_config = self._yaml

    def _yaml_returns(self, conf):
        async def fake(hass, name):
            return None if conf is None else {DOMAIN: conf}
        integration.async_integration_yaml_config = fake

    def _setup(self, conf, state="380"):
        hass = RunningHass({"s": FakeState(state)})
        ok = asyncio.run(integration.async_setup(hass, {DOMAIN: conf}))
        return hass, ok

    def test_setup_starts_updater_and_sends(self):
        hass, ok = self._setup({**CREDENTIALS, "widgets": WIDGETS})

        self.assertTrue(ok)
        self.assertEqual(RecordingAPI.sent, ["P 380W"])
        self.assertIsNotNone(hass.data[DOMAIN]["updater"])
        self.assertIn("reload", hass.registered)
        self.assertIn("refresh", hass.registered)

    def test_invalid_yaml_fails_setup(self):
        hass, ok = self._setup({**CREDENTIALS, "max_items": 0})
        self.assertFalse(ok)
        self.assertEqual(RecordingAPI.sent, [])

    def test_widgets_only_yaml_waits_for_the_config_entry(self):
        hass, ok = self._setup({"widgets": WIDGETS})

        self.assertTrue(ok)
        self.assertEqual(RecordingAPI.sent, [])
        self.assertNotIn("updater", hass.data[DOMAIN])
        self.assertEqual(len(hass.data[DOMAIN]["yaml_settings"].widgets), 1)

    def test_reload_applies_a_changed_configuration(self):
        hass, _ = self._setup({**CREDENTIALS, "widgets": WIDGETS})
        first_updater = hass.data[DOMAIN]["updater"]

        # the widget gets another icon in configuration.yaml
        self._yaml_returns({
            **CREDENTIALS,
            "language": "en",
            "widgets": [{**WIDGETS[0], "icon": "W"}],
        })
        # the rate limit has long passed
        first_updater._last_send = 0.0

        ok = asyncio.run(integration.async_reload(hass))

        self.assertTrue(ok)
        self.assertEqual(RecordingAPI.sent, ["P 380W", "W 380W"])
        self.assertEqual(hass.data[DOMAIN]["language"], "en")
        self.assertIsNot(hass.data[DOMAIN]["updater"], first_updater)

    def test_reload_respects_the_rate_limit(self):
        # Reloading right after a send must not bypass the 60 s limit:
        # the new line shows up in the preview entity at once and is
        # transmitted by the scheduled retry.
        hass, _ = self._setup({**CREDENTIALS, "widgets": WIDGETS})

        self._yaml_returns({
            **CREDENTIALS,
            "widgets": [{**WIDGETS[0], "icon": "W"}],
        })
        asyncio.run(integration.async_reload(hass))

        updater = hass.data[DOMAIN]["updater"]
        state, attrs = hass.set_states["sensor.switchbot_dashboard"]

        self.assertEqual(RecordingAPI.sent, ["P 380W"])
        self.assertEqual(state, "W 380W")
        self.assertFalse(attrs["sent_to_device"])
        self.assertIsNotNone(updater._cancel_retry)

    def test_reload_does_not_resend_an_unchanged_dashboard(self):
        hass, _ = self._setup({**CREDENTIALS, "widgets": WIDGETS})

        self._yaml_returns({**CREDENTIALS, "widgets": WIDGETS})
        asyncio.run(integration.async_reload(hass))

        self.assertEqual(RecordingAPI.sent, ["P 380W"])

    def test_reload_with_invalid_config_keeps_the_running_one(self):
        hass, _ = self._setup({**CREDENTIALS, "widgets": WIDGETS})
        updater = hass.data[DOMAIN]["updater"]

        self._yaml_returns({**CREDENTIALS, "widgets": [{"type": "nix"}]})
        ok = asyncio.run(integration.async_reload(hass))

        self.assertFalse(ok)
        self.assertIs(hass.data[DOMAIN]["updater"], updater)
        self.assertEqual(len(hass.data[DOMAIN]["widgets"]), 1)

    def test_reload_survives_a_yaml_read_error(self):
        hass, _ = self._setup({**CREDENTIALS, "widgets": WIDGETS})
        updater = hass.data[DOMAIN]["updater"]

        async def broken(hass, name):
            raise RuntimeError("yaml kaputt")

        integration.async_integration_yaml_config = broken

        self.assertFalse(asyncio.run(integration.async_reload(hass)))
        self.assertIs(hass.data[DOMAIN]["updater"], updater)

    def test_reload_without_yaml_block_fails_for_yaml_setups(self):
        hass, _ = self._setup({**CREDENTIALS, "widgets": WIDGETS})
        self._yaml_returns(None)
        self.assertFalse(asyncio.run(integration.async_reload(hass)))

    def test_reload_into_dry_run_stops_sending(self):
        hass, _ = self._setup({**CREDENTIALS, "widgets": WIDGETS})

        self._yaml_returns({
            **CREDENTIALS, "dry_run": True,
            "widgets": [{**WIDGETS[0], "icon": "W"}],
        })
        asyncio.run(integration.async_reload(hass))

        self.assertEqual(RecordingAPI.sent, ["P 380W"])
        state, attrs = hass.set_states["sensor.switchbot_dashboard"]
        self.assertEqual(state, "W 380W")
        self.assertFalse(attrs["sent_to_device"])

    def test_auto_refresh_off_starts_no_updater(self):
        hass, ok = self._setup({
            **CREDENTIALS, "auto_refresh": False, "widgets": WIDGETS,
        })
        self.assertTrue(ok)
        self.assertIsNone(hass.data[DOMAIN].get("updater"))
        self.assertEqual(RecordingAPI.sent, [])

    def test_tracker_is_created_once_and_kept_across_reloads(self):
        hass, _ = self._setup({**CREDENTIALS, "widgets": WIDGETS})
        tracker = hass.data[DOMAIN]["tracker"]

        self._yaml_returns({**CREDENTIALS, "widgets": WIDGETS})
        asyncio.run(integration.async_reload(hass))

        self.assertIs(hass.data[DOMAIN]["tracker"], tracker)


class ConfigEntryTest(unittest.TestCase):
    """UI setup: credentials from the entry, options on top of YAML."""

    def setUp(self):
        RecordingAPI.sent = []
        self._api = integration.SwitchBotAPI
        integration.SwitchBotAPI = RecordingAPI

    def tearDown(self):
        integration.SwitchBotAPI = self._api

    def _entry(self, options):
        listeners = []
        return types.SimpleNamespace(
            data=dict(CREDENTIALS),
            options=options,
            entry_id="abc",
            add_update_listener=lambda listener: (
                listeners.append(listener) or (lambda: None)
            ),
            async_on_unload=lambda unsub: None,
            listeners=listeners,
        )

    def test_entry_uses_yaml_widgets_and_its_own_options(self):
        hass = RunningHass({"s": FakeState("380")})

        asyncio.run(integration.async_setup(
            hass, {DOMAIN: {"widgets": WIDGETS, "language": "de"}}
        ))
        entry = self._entry({"language": "en", "max_items": 2})
        ok = asyncio.run(integration.async_setup_entry(hass, entry))

        self.assertTrue(ok)
        self.assertEqual(RecordingAPI.sent, ["P 380W"])
        self.assertEqual(hass.data[DOMAIN]["language"], "en")
        self.assertEqual(hass.data[DOMAIN]["max_items"], 2)
        self.assertEqual(len(entry.listeners), 1)

    def test_unload_stops_the_updater(self):
        hass = RunningHass({"s": FakeState("380")})
        entry = self._entry({})

        asyncio.run(integration.async_setup_entry(hass, entry))
        self.assertIsNotNone(hass.data[DOMAIN]["updater"])

        asyncio.run(integration.async_unload_entry(hass, entry))
        self.assertIsNone(hass.data[DOMAIN]["updater"])


if __name__ == "__main__":
    unittest.main()
