"""Tests for the widget editor (config subentries) and the YAML import.

Run (from the repo root):

    python3 custom_components/switchbot_dashboard/tests/test_widget_editor.py
"""

import asyncio
import json
import types
import unittest
from pathlib import Path

import helpers  # noqa: F401  (stubs HA/aiohttp, sets sys.path)
from helpers import FakeState
from test_settings import CREDENTIALS, RecordingAPI, RunningHass

import custom_components.switchbot_dashboard as integration
from custom_components.switchbot_dashboard.config.schema import ConfigError
from custom_components.switchbot_dashboard.const import DOMAIN
from custom_components.switchbot_dashboard.settings import OPTION_KEYS
from custom_components.switchbot_dashboard.widget_forms import (
    SUBENTRY_TYPE,
    clean_input,
    describe_fields,
    import_payload,
    validate_widget,
    widget_title,
    widget_types,
)
from custom_components.switchbot_dashboard.widgets.registry import (
    get_registration,
)

PACKAGE = Path(__file__).resolve().parents[1]

# a configuration like the one in use, shortened
YAML_WIDGETS = [
    {"type": "weather", "temperature_entity": "sensor.out",
     "trend_entity": "sensor.trend", "reference_entity": "sensor.dwd",
     "priority": 100},
    {"type": "entity", "entity": "s", "icon": "P", "formatter": "power",
     "priority": 200},
    {"type": "window", "mode": "state", "group": "balkon",
     "entities": {"sensor.b1": "Balkon 1", "sensor.b2": "Balkon 2"}},
    {"type": "door", "lock_entity": "lock.door",
     "contact_entity": "binary_sensor.door"},
    {"type": "appliance", "name": "GS", "running_entity": "sensor.gs",
     "done_entity": "input_boolean.gs", "icon": "🍽", "priority": 720},
    {"type": "alert", "name": "Balkon offen", "group": "balkon",
     "priority": 50, "conditions": [
         {"entity": "sensor.b1", "state": "Offen"},
         {"entity": "person.me", "not_state": "home"}]},
]


class FormTest(unittest.TestCase):

    def test_every_type_has_a_form(self):
        kinds = {"entity", "text", "int", "float", "bool", "select", "object"}
        for widget_type in widget_types():
            specs = describe_fields(widget_type)
            self.assertTrue(specs, widget_type)
            self.assertTrue({s.kind for s in specs} <= kinds, widget_type)
            required = {s.name for s in specs if s.required}
            self.assertEqual(
                required, set(get_registration(widget_type).required),
                widget_type,
            )
            self.assertNotIn("type", {s.name for s in specs})

    def test_field_kinds(self):
        weather = {s.name: s for s in describe_fields("weather")}
        self.assertEqual(weather["reference_entity"].kind, "entity")
        self.assertEqual(weather["hysteresis"].kind, "float")
        self.assertEqual(weather["hysteresis"].default, 0.75)
        self.assertIsNone(weather["icon"].default)   # widget default

        window = {s.name: s for s in describe_fields("window")}
        self.assertEqual(window["mode"].kind, "select")
        self.assertEqual(window["mode"].choices, ("rooms", "state"))
        self.assertEqual(window["entities"].kind, "object")

        alert = {s.name: s for s in describe_fields("alert")}
        self.assertEqual(alert["conditions"].kind, "object")

    def test_name_and_entities_come_first(self):
        names = [s.name for s in describe_fields("appliance")]
        self.assertEqual(names[0], "name")

    def test_clean_input(self):
        data = clean_input("appliance", {
            "name": "WM", "running_entity": "sensor.wm", "icon": "",
            "priority": 700.0, "done_entity": None, "unknown": "x",
        })
        self.assertEqual(data, {
            "type": "appliance", "name": "WM",
            "running_entity": "sensor.wm", "priority": 700,
        })
        self.assertIsInstance(data["priority"], int)

    def test_validation_reports_missing_fields(self):
        with self.assertRaises(ConfigError):
            validate_widget({"type": "appliance", "name": "WM"})
        validate_widget({"type": "appliance", "name": "WM",
                         "running_entity": "sensor.wm"})

    def test_titles(self):
        self.assertEqual(widget_title(YAML_WIDGETS[0]), "Weather: sensor.out")
        self.assertEqual(widget_title(YAML_WIDGETS[2]),
                         "Window: Balkon 1, Balkon 2")
        self.assertEqual(widget_title(YAML_WIDGETS[4]), "Appliance: GS")
        self.assertEqual(widget_title({"type": "waste"}), "Waste")


class TranslationTest(unittest.TestCase):

    def test_all_fields_and_types_have_labels(self):
        fields = {s.name for t in widget_types() for s in describe_fields(t)}
        for path in ("strings.json", "translations/en.json",
                     "translations/de.json"):
            data = json.loads((PACKAGE / path).read_text(encoding="utf-8"))
            widget = data["config_subentries"][SUBENTRY_TYPE]
            for step in ("widget", "reconfigure"):
                labels = widget["step"][step]["data"]
                self.assertEqual(set(labels), fields, (path, step))
            options = data["selector"]["widget_type"]["options"]
            self.assertEqual(set(options), set(widget_types()), path)
            self.assertIn("yaml_migrated", data["issues"])


class ImportTest(unittest.TestCase):

    def test_payload_splits_credentials_options_widgets(self):
        conf = {**CREDENTIALS, "dry_run": False, "max_items": 4,
                "widgets": YAML_WIDGETS}
        payload = import_payload(conf, OPTION_KEYS)

        self.assertEqual(payload["data"], CREDENTIALS)
        self.assertEqual(payload["options"],
                         {"dry_run": False, "max_items": 4})
        self.assertEqual(payload["widgets"], YAML_WIDGETS)
        # copies, so the subentries do not share the YAML objects
        self.assertIsNot(payload["widgets"][0], YAML_WIDGETS[0])
        # what HA stores must be plain JSON
        json.dumps(payload)

    def test_imported_widgets_are_valid(self):
        for widget in YAML_WIDGETS:
            validate_widget(widget)


class FakeConfigEntries:

    def __init__(self, entries=()):
        self.entries = list(entries)
        self.started_flows = []
        self.flow = types.SimpleNamespace(async_init=self._init)

    def async_entries(self, domain):
        return list(self.entries)

    result = {"type": "create_entry"}

    async def _init(self, domain, context=None, data=None):
        self.started_flows.append((domain, context, data))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class UiHass(RunningHass):

    def __init__(self, states=None, entries=()):
        super().__init__(states)
        self.config_entries = FakeConfigEntries(entries)
        self.tasks = []

    def async_create_task(self, coro):
        self.tasks.append(coro)


def subentry(data, kind=SUBENTRY_TYPE, title="w"):
    return types.SimpleNamespace(subentry_type=kind, data=data, title=title)


def entry(subentries=(), options=None):
    return types.SimpleNamespace(
        data=dict(CREDENTIALS), options=options or {}, entry_id="e1",
        subentries={str(i): s for i, s in enumerate(subentries)},
        add_update_listener=lambda listener: (lambda: None),
        async_on_unload=lambda unsub: None,
    )


class SetupTest(unittest.TestCase):

    def setUp(self):
        RecordingAPI.sent = []
        self._api = integration.SwitchBotAPI
        integration.SwitchBotAPI = RecordingAPI

    def tearDown(self):
        integration.SwitchBotAPI = self._api

    def test_full_yaml_block_is_imported_once(self):
        hass = UiHass({"s": FakeState("380")})
        conf = {**CREDENTIALS, "widgets": YAML_WIDGETS[1:2]}

        ok = asyncio.run(integration.async_setup(hass, {DOMAIN: conf}))
        for task in hass.tasks:
            asyncio.run(task)

        self.assertTrue(ok)
        self.assertEqual(len(hass.config_entries.started_flows), 1)
        domain, context, data = hass.config_entries.started_flows[0]
        self.assertEqual(context, {"source": "import"})
        self.assertEqual(data["widgets"], YAML_WIDGETS[1:2])
        # the import's config entry starts the dashboard, not YAML
        self.assertEqual(RecordingAPI.sent, [])

    def test_failed_import_keeps_running_from_yaml(self):
        hass = UiHass({"s": FakeState("380")})
        hass.config_entries.result = RuntimeError("no subentries here")
        conf = {**CREDENTIALS, "widgets": YAML_WIDGETS[1:2]}

        asyncio.run(integration.async_setup(hass, {DOMAIN: conf}))
        with self.assertLogs("custom_components.switchbot_dashboard",
                             "ERROR"):
            for task in hass.tasks:
                asyncio.run(task)

        self.assertEqual(RecordingAPI.sent, ["P 380W"])

    def test_yaml_is_ignored_once_an_entry_exists(self):
        hass = UiHass({"s": FakeState("380")}, entries=[object()])
        conf = {**CREDENTIALS, "widgets": YAML_WIDGETS[1:2]}

        with self.assertLogs("custom_components.switchbot_dashboard",
                             "WARNING"):
            asyncio.run(integration.async_setup(hass, {DOMAIN: conf}))

        self.assertEqual(hass.config_entries.started_flows, [])
        self.assertEqual(RecordingAPI.sent, [])
        self.assertIsNone(hass.data[DOMAIN].get("updater"))

    def test_entry_widgets_come_from_subentries(self):
        hass = UiHass({"s": FakeState("380"), "w": FakeState("on")})
        ui_entry = entry([
            subentry({"type": "entity", "entity": "s", "icon": "P",
                      "formatter": "power"}),
        ])

        ok = asyncio.run(integration.async_setup_entry(hass, ui_entry))

        self.assertTrue(ok)
        self.assertEqual(RecordingAPI.sent, ["P 380W"])

    def test_subentries_win_over_yaml_widgets(self):
        hass = UiHass({"s": FakeState("380"), "t": FakeState("21.4")})
        asyncio.run(integration.async_setup(hass, {DOMAIN: {
            "widgets": [{"type": "entity", "entity": "t", "icon": "T"}],
        }}))
        ui_entry = entry([
            subentry({"type": "entity", "entity": "s", "icon": "P",
                      "formatter": "power"}),
        ])

        asyncio.run(integration.async_setup_entry(hass, ui_entry))

        self.assertEqual(RecordingAPI.sent, ["P 380W"])

    def test_without_subentries_yaml_widgets_still_work(self):
        hass = UiHass({"t": FakeState("21")})
        asyncio.run(integration.async_setup(hass, {DOMAIN: {
            "widgets": [{"type": "entity", "entity": "t", "icon": "T"}],
        }}))

        asyncio.run(integration.async_setup_entry(hass, entry()))

        self.assertEqual(RecordingAPI.sent, ["T 21"])

    def test_invalid_subentry_is_skipped(self):
        hass = UiHass({"s": FakeState("380")})
        ui_entry = entry([
            subentry({"type": "appliance", "name": "broken"}, title="bad"),
            subentry({"type": "entity", "entity": "s", "icon": "P",
                      "formatter": "power"}),
            subentry({"other": 1}, kind="something_else"),
        ])

        with self.assertLogs("custom_components.switchbot_dashboard",
                             "ERROR"):
            asyncio.run(integration.async_setup_entry(hass, ui_entry))

        self.assertEqual(RecordingAPI.sent, ["P 380W"])


if __name__ == "__main__":
    unittest.main()
