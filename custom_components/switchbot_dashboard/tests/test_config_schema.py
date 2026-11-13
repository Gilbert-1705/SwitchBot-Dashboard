"""Tests for YAML configuration, validation and registry.

Run (from the repo root):

    python3 custom_components/switchbot_dashboard/tests/test_config_schema.py
"""

import unittest

import helpers  # noqa: F401  (stubs HA/aiohttp, sets sys.path)
from helpers import FakeHass, FakeState

from custom_components.switchbot_dashboard.config.schema import (
    ConfigError,
    build_widget_configs,
)
from custom_components.switchbot_dashboard.formatters.factory import (
    FormatterFactory,
)
from custom_components.switchbot_dashboard.formatters.base import (
    BaseFormatter,
)
from custom_components.switchbot_dashboard.widgets.base import BaseWidget
from custom_components.switchbot_dashboard.widgets.config_models import (
    WidgetConfig,
)
from custom_components.switchbot_dashboard.widgets.manager import (
    WidgetManager,
)
from custom_components.switchbot_dashboard.widgets.registry import (
    register_widget_type,
)


class BuildConfigsTest(unittest.TestCase):

    def test_full_yaml_config(self):

        configs = build_widget_configs([
            {"type": "weather"},
            {
                "type": "entity",
                "entity": "sensor.power",
                "icon": "P",
                "formatter": "power",
                "priority": 200,
            },
            {
                "type": "window",
                "entities": {"binary_sensor.b1": "Balkon"},
                "mode": "state",
            },
            {"type": "door", "lock_entity": "lock.tuer"},
            {"type": "waste", "entity": "sensor.muell", "days": 2},
            {
                "type": "calendar",
                "entity": "calendar.geburtstage",
                "icon": "🎂",
                "days": 1,
            },
            {"type": "presence", "entities": {"person.jan": "Jan"}},
            {
                "type": "fuel",
                "level_entity": "sensor.tank",
                "price_entity": "sensor.preis",
                "min_level": 20,
                "max_price": "1.75",
            },
            {
                "type": "appliance",
                "name": "WM",
                "running_entity": "sensor.wm",
                "done_entity": "input_boolean.wm",
            },
        ])

        self.assertEqual(len(configs), 9)
        self.assertEqual(configs[1].priority, 200)
        self.assertEqual(configs[2].mode, "state")
        self.assertEqual(configs[4].days, 2)
        # numbers are coerced, even from strings
        self.assertEqual(configs[7].max_price, 1.75)

    def test_unknown_type_lists_available(self):
        with self.assertRaises(ConfigError) as ctx:
            build_widget_configs([{"type": "foo"}])
        self.assertIn("unknown type 'foo'", str(ctx.exception))
        self.assertIn("weather", str(ctx.exception))

    def test_missing_type(self):
        with self.assertRaises(ConfigError) as ctx:
            build_widget_configs([{"entity": "sensor.x"}])
        self.assertIn("missing 'type'", str(ctx.exception))

    def test_unknown_option_lists_available(self):
        with self.assertRaises(ConfigError) as ctx:
            build_widget_configs([
                {"type": "waste", "entitty": "sensor.x"},
            ])
        self.assertIn("unknown option 'entitty'", str(ctx.exception))
        self.assertIn("entity", str(ctx.exception))

    def test_missing_required_option(self):
        with self.assertRaises(ConfigError) as ctx:
            build_widget_configs([{"type": "fuel"}])
        self.assertIn("missing required option 'level_entity'",
                      str(ctx.exception))

    def test_invalid_mode(self):
        with self.assertRaises(ConfigError) as ctx:
            build_widget_configs([
                {
                    "type": "window",
                    "entities": {"a": "A"},
                    "mode": "banana",
                },
            ])
        self.assertIn("must be one of rooms, state", str(ctx.exception))

    def test_invalid_number(self):
        with self.assertRaises(ConfigError) as ctx:
            build_widget_configs([
                {
                    "type": "waste",
                    "entity": "sensor.x",
                    "days": "bald",
                },
            ])
        self.assertIn("'days' must be a number", str(ctx.exception))

    def test_invalid_entities_mapping(self):
        with self.assertRaises(ConfigError) as ctx:
            build_widget_configs([
                {"type": "presence", "entities": ["person.jan"]},
            ])
        self.assertIn("mapping of entity_id to name", str(ctx.exception))

    def test_error_names_widget_position(self):
        with self.assertRaises(ConfigError) as ctx:
            build_widget_configs([
                {"type": "weather"},
                {"type": "fuel"},
            ])
        self.assertIn("Widget 2 (fuel)", str(ctx.exception))


class CustomWidgetTest(unittest.TestCase):
    """Custom widgets: registry + manager + validation."""

    def test_custom_widget_roundtrip(self):

        class HelloWidget(BaseWidget):

            def __init__(self, hass, priority=100):
                super().__init__(hass)
                self.priority = priority

            def render(self):
                return None

        register_widget_type("hello", HelloWidget, WidgetConfig)

        configs = build_widget_configs([
            {"type": "hello", "priority": 42},
        ])

        manager = WidgetManager(hass=None, configs=configs)
        widgets = manager.widgets()

        self.assertEqual(len(widgets), 1)
        self.assertIsInstance(widgets[0], HelloWidget)
        self.assertEqual(widgets[0].priority, 42)


class FormatterRegistryTest(unittest.TestCase):

    def test_register_custom_formatter(self):

        class EuroFormatter(BaseFormatter):
            def format(self, value):
                return f"{value}€"

        FormatterFactory.register("euro", EuroFormatter)

        self.assertEqual(
            FormatterFactory.create("euro").format("1.65"),
            "1.65€",
        )

    def test_unknown_formatter_falls_back(self):
        formatter = FormatterFactory.create("gibtsnicht")
        self.assertEqual(formatter.format("x"), "x")


if __name__ == "__main__":
    unittest.main()
