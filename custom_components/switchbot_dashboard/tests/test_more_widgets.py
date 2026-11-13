"""Tests for the threshold, status and wallbox widgets.

Run (from the repo root):

    python3 custom_components/switchbot_dashboard/tests/test_more_widgets.py
"""

import unittest

import helpers  # noqa: F401  (stubs HA/aiohttp, sets sys.path)
from helpers import FakeHass, FakeState

from custom_components.switchbot_dashboard.config.schema import (
    ConfigError,
    build_widget_configs,
)
from custom_components.switchbot_dashboard.const import DOMAIN
from custom_components.switchbot_dashboard.icons import Icons
from custom_components.switchbot_dashboard.render import render_dashboard
from custom_components.switchbot_dashboard.text import state_text
from custom_components.switchbot_dashboard.widgets.alert import AlertWidget
from custom_components.switchbot_dashboard.widgets.status import (
    StatusWidget,
)
from custom_components.switchbot_dashboard.widgets.threshold import (
    ThresholdWidget,
)
from custom_components.switchbot_dashboard.widgets.wallbox import (
    WallboxWidget,
)


class ThresholdWidgetTest(unittest.TestCase):

    def _co2(self, value, **kwargs):
        hass = FakeHass({"co2": FakeState(value)})
        options = {"above": 1000, "critical_above": 1500}
        options.update(kwargs)
        return ThresholdWidget(
            hass, entity="co2", icon="☁", name="CO₂", **options
        ).render()

    def test_hidden_inside_the_bounds(self):
        self.assertIsNone(self._co2("620"))

    def test_shown_above_the_bound(self):
        item = self._co2("1210")
        self.assertEqual(item.value, "CO₂ 1210")
        self.assertEqual(item.importance, 55)

    def test_critical_is_always_shown(self):
        item = self._co2("1800")
        self.assertEqual(item.value, "CO₂ 1800")
        self.assertEqual(item.importance, 85)

    def test_bound_itself_is_still_fine(self):
        self.assertIsNone(self._co2("1000"))

    def test_below_bound_for_cheap_electricity(self):
        hass = FakeHass({"preis": FakeState("17.6")})
        item = ThresholdWidget(
            hass, entity="preis", icon="€", below=20, unit="ct",
            precision=1, importance=40,
        ).render()
        self.assertEqual(item.value, "17.6ct")
        self.assertEqual(item.importance, 40)

    def test_two_sided_bounds(self):
        def humidity(value):
            hass = FakeHass({"h": FakeState(value)})
            return ThresholdWidget(
                hass, entity="h", icon="💧", below=35, above=65, unit="%"
            ).render()

        self.assertEqual(humidity("28").value, "28%")
        self.assertIsNone(humidity("50"))
        self.assertEqual(humidity("71").value, "71%")

    def test_no_numeric_value_is_hidden(self):
        self.assertIsNone(self._co2("unavailable"))
        hass = FakeHass({})
        self.assertIsNone(
            ThresholdWidget(hass, entity="x", icon="x", above=1).render()
        )

    def test_yaml_needs_at_least_one_bound(self):
        with self.assertRaises(ConfigError) as ctx:
            build_widget_configs([
                {"type": "threshold", "entity": "sensor.co2", "icon": "☁"},
            ])
        self.assertIn("at least one of above", str(ctx.exception))

    def test_yaml_numbers_are_coerced(self):
        configs = build_widget_configs([{
            "type": "threshold", "entity": "sensor.co2", "icon": "☁",
            "above": "1000", "critical_above": 1500,
        }])
        self.assertEqual(configs[0].above, 1000.0)
        self.assertIsNone(configs[0].below)

    def test_yaml_rejects_a_non_numeric_bound(self):
        with self.assertRaises(ConfigError) as ctx:
            build_widget_configs([{
                "type": "threshold", "entity": "sensor.co2", "icon": "☁",
                "above": "viel",
            }])
        self.assertIn("'above' must be a number", str(ctx.exception))


class StatusWidgetTest(unittest.TestCase):

    ENTITIES = {"nas": "NAS", "vpn": "VPN", "dns": "DNS"}

    def _render(self, nas="on", vpn="on", dns="on", **kwargs):
        hass = FakeHass({
            "nas": FakeState(nas),
            "vpn": FakeState(vpn),
            "dns": FakeState(dns),
        })
        return StatusWidget(hass, entities=self.ENTITIES, **kwargs).render()

    def test_all_fine_is_hidden(self):
        self.assertIsNone(self._render())

    def test_one_down(self):
        item = self._render(nas="off")
        self.assertEqual(item.value, "NAS")
        self.assertEqual(item.icon, Icons.WARNING)
        self.assertEqual(item.importance, 85)

    def test_several_down_are_joined(self):
        self.assertEqual(self._render(nas="off", vpn="off").value, "NAS+VPN")
        self.assertEqual(
            self._render(nas="off", vpn="off", dns="off").value, "NAS+2"
        )

    def test_unavailable_counts_as_down(self):
        self.assertEqual(self._render(vpn="unavailable").value, "VPN")

    def test_unavailable_can_be_ignored(self):
        self.assertIsNone(
            self._render(vpn="unavailable", unavailable_is_problem=False)
        )

    def test_missing_entity_counts_as_down(self):
        hass = FakeHass({})
        item = StatusWidget(hass, entities={"nas": "NAS"}).render()
        self.assertEqual(item.value, "NAS")

    def test_custom_ok_states(self):
        self.assertIsNone(self._render(nas="idle", ok_states=["idle", "on"]))
        self.assertEqual(
            self._render(nas="on", vpn="on", dns="on",
                         ok_states=["idle"]).value,
            "NAS+2",
        )

    def test_states_are_compared_case_insensitively(self):
        self.assertIsNone(self._render(nas="Online", vpn="UP"))

    def test_unquoted_yaml_on_is_understood(self):
        # YAML turns "ok_states: [on]" into [True]
        configs = build_widget_configs([{
            "type": "status",
            "entities": {"nas": "NAS"},
            "ok_states": [True],
        }])
        self.assertEqual(configs[0].ok_states, ["on"])

        hass = FakeHass({"nas": FakeState("on")})
        self.assertEqual(render_dashboard(hass, configs), "")


class WallboxWidgetTest(unittest.TestCase):

    def _render(self, status, power=None, language=None):
        states = {"wb": FakeState(status)}
        if power is not None:
            states["p"] = FakeState(power)
        hass = FakeHass(states)
        if language:
            hass.data[DOMAIN] = {"language": language}
        return WallboxWidget(
            hass, status_entity="wb", power_entity="p", name="WB"
        ).render()

    def test_idle_is_hidden(self):
        self.assertIsNone(self._render("available"))
        self.assertIsNone(self._render("unknown"))

    def test_charging_with_power(self):
        item = self._render("charging", power="7400")
        self.assertEqual(item.value, "WB 7.4kW")
        self.assertEqual(item.importance, 30)

    def test_charging_without_power_reading(self):
        self.assertEqual(self._render("charging").value, "WB lädt")
        self.assertEqual(
            self._render("charging", power="unknown").value, "WB lädt"
        )

    def test_finished(self):
        item = self._render("complete")
        self.assertEqual(item.value, "WB Voll")
        self.assertEqual(item.importance, 45)

    def test_error_needs_attention(self):
        item = self._render("error")
        self.assertEqual(item.value, "WB Fehler")
        self.assertEqual(item.importance, 85)

    def test_english(self):
        self.assertEqual(
            self._render("charging", language="en").value, "WB charging"
        )
        self.assertEqual(
            self._render("complete", language="en").value, "WB Full"
        )
        self.assertEqual(
            self._render("error", language="en").value, "WB Error"
        )

    def test_missing_entity(self):
        hass = FakeHass({})
        self.assertIsNone(WallboxWidget(hass, status_entity="wb").render())


class YamlBooleanStatesTest(unittest.TestCase):
    """An unquoted on/off in YAML arrives as a boolean."""

    def test_state_text(self):
        self.assertEqual(state_text(True), "on")
        self.assertEqual(state_text(False), "off")
        self.assertEqual(state_text("Offen"), "Offen")
        self.assertEqual(state_text(5), "5")

    def test_alert_condition_with_unquoted_on(self):
        # "state: on" without quotes used to never match
        hass = FakeHass({"tuer": FakeState("on")})
        item = AlertWidget(
            hass, name="Tür", conditions=[{"entity": "tuer", "state": True}]
        ).render()
        self.assertIsNotNone(item)

    def test_alert_condition_with_unquoted_off(self):
        hass = FakeHass({"tuer": FakeState("off")})
        widget = AlertWidget(
            hass, name="x",
            conditions=[{"entity": "tuer", "not_state": False}],
        )
        self.assertIsNone(widget.render())


class RegistryTest(unittest.TestCase):

    def test_new_types_are_configurable_via_yaml(self):
        configs = build_widget_configs([
            {"type": "threshold", "entity": "sensor.co2", "icon": "☁",
             "name": "CO₂", "above": 1000},
            {"type": "status", "entities": {"binary_sensor.nas": "NAS"}},
            {"type": "wallbox", "status_entity": "sensor.wb",
             "power_entity": "sensor.wb_power", "name": "WB"},
        ])
        self.assertEqual(
            [c.type for c in configs], ["threshold", "status", "wallbox"]
        )

    def test_they_render_through_the_pipeline(self):
        configs = build_widget_configs([
            {"type": "threshold", "entity": "co2", "icon": "☁",
             "name": "CO₂", "above": 1000},
            {"type": "status", "entities": {"nas": "NAS"}},
            {"type": "wallbox", "status_entity": "wb", "name": "WB"},
        ])
        hass = FakeHass({
            "co2": FakeState("1300"),
            "nas": FakeState("off"),
            "wb": FakeState("charging"),
        })
        self.assertEqual(
            render_dashboard(hass, configs),
            "! NAS   🔌 WB lädt   ☁ CO₂ 1300",
        )


if __name__ == "__main__":
    unittest.main()
