"""Tests for sprint 4: text shortening, presence, fuel widget.

Run (from the repo root):

    python3 custom_components/switchbot_dashboard/tests/test_sprint4.py
"""

import unittest

import helpers  # noqa: F401  (stubs HA/aiohttp, sets sys.path)
from helpers import FakeHass, FakeState

from custom_components.switchbot_dashboard.icons import Icons
from custom_components.switchbot_dashboard.text import (
    cap_bytes,
    join_names,
    shorten,
)
from custom_components.switchbot_dashboard.widgets.fuel import FuelWidget
from custom_components.switchbot_dashboard.widgets.presence import (
    PresenceWidget,
)
from custom_components.switchbot_dashboard.widgets.window import WindowWidget


class TextTest(unittest.TestCase):

    def test_short_text_unchanged(self):
        self.assertEqual(shorten("Oma", 10), "Oma")

    def test_long_text_gets_ellipsis(self):
        self.assertEqual(shorten("Max Mustermann", 10), "Max Muste…")

    def test_join_two_names(self):
        self.assertEqual(join_names(["Wohnen", "Essen"]), "Wohnen+Essen")

    def test_join_many_names_collapses(self):
        self.assertEqual(
            join_names(["Wohnen", "Essen", "Küche"]),
            "Wohnen+2",
        )

    def test_cap_bytes_short_text_unchanged(self):
        self.assertEqual(cap_bytes("Hallo", 300), "Hallo")

    def test_cap_bytes_truncates_at_limit(self):
        self.assertEqual(cap_bytes("abcdef", 3), "abc")

    def test_cap_bytes_does_not_split_multibyte_chars(self):
        # 🎂 takes 4 bytes: a limit of 5 must not produce a
        # broken half character
        result = cap_bytes("a🎂b", 5)
        self.assertEqual(result, "a🎂")
        result.encode("utf-8")  # must stay valid UTF-8

    def test_cap_bytes_realistic_dashboard_line(self):
        line = "🌡 21°C ☀   ○ Offen   🗑 Rest Heute   🎂 Oma   ⛽ 1.64"
        self.assertEqual(cap_bytes(line, 300), line)
        self.assertLess(len(line.encode("utf-8")), 300)


class WindowShorteningTest(unittest.TestCase):

    def test_three_open_rooms_collapse(self):
        hass = FakeHass({
            "a": FakeState("on"),
            "b": FakeState("on"),
            "c": FakeState("on"),
        })
        widget = WindowWidget(
            hass,
            entities={"a": "Wohnen", "b": "Essen", "c": "Küche"},
        )
        self.assertEqual(widget.render().value, "Wohnen+2")


class WindowStatesTest(unittest.TestCase):
    """Homematic states: Offen, Geschlossen, Gekippt, unknown."""

    ENTITIES = {"a": "Wohnen", "b": "Essen"}

    def _render(self, a, b):
        hass = FakeHass({
            "a": FakeState(a),
            "b": FakeState(b),
        })
        return WindowWidget(hass, entities=self.ENTITIES).render()

    def test_german_states_all_closed(self):
        item = self._render("Geschlossen", "Geschlossen")
        self.assertEqual(item.value, "●")

    def test_offen_is_open(self):
        item = self._render("Offen", "Geschlossen")
        self.assertEqual(item.value, "Wohnen")
        self.assertEqual(item.importance, 65)

    def test_gekippt_shows_but_less_important(self):
        item = self._render("Gekippt", "Geschlossen")
        self.assertEqual(item.value, "Wohnen")
        self.assertEqual(item.importance, 40)

    def test_open_beats_tilted_importance(self):
        item = self._render("Gekippt", "Offen")
        self.assertEqual(item.value, "Essen+Wohnen")
        self.assertEqual(item.importance, 65)

    def test_unknown_is_skipped(self):
        item = self._render("unknown", "Geschlossen")
        self.assertEqual(item.value, "●")


class WindowStateModeTest(unittest.TestCase):
    """mode='state': state instead of room names (balcony doors)."""

    ENTITIES = {"a": "Balkon 1", "b": "Balkon 2"}

    def _render(self, a, b):
        hass = FakeHass({
            "a": FakeState(a),
            "b": FakeState(b),
        })
        return WindowWidget(
            hass, entities=self.ENTITIES, mode="state"
        ).render()

    def test_all_closed(self):
        item = self._render("Geschlossen", "Geschlossen")
        self.assertEqual(item.value, "●")

    def test_open_shows_state_not_names(self):
        item = self._render("Offen", "Geschlossen")
        self.assertEqual(item.value, "Offen")
        self.assertEqual(item.importance, 65)

    def test_both_open_still_short(self):
        item = self._render("Offen", "Offen")
        self.assertEqual(item.value, "Offen")

    def test_tilted_is_background_info(self):
        item = self._render("Gekippt", "Gekippt")
        self.assertEqual(item.value, "Gekippt")
        self.assertEqual(item.importance, 25)

    def test_mixed_states(self):
        item = self._render("Offen", "Gekippt")
        self.assertEqual(item.value, "Offen+Gekippt")
        self.assertEqual(item.importance, 65)


class PresenceWidgetTest(unittest.TestCase):

    ENTITIES = {"p1": "Jan", "p2": "Anna"}

    def _render(self, p1, p2):
        hass = FakeHass({
            "p1": FakeState(p1),
            "p2": FakeState(p2),
        })
        return PresenceWidget(hass, entities=self.ENTITIES).render()

    def test_one_person_home(self):
        item = self._render("home", "not_home")
        self.assertEqual(item.value, "Jan")
        self.assertEqual(item.icon, Icons.HOME)

    def test_two_persons_home(self):
        item = self._render("home", "home")
        self.assertEqual(item.value, "Jan+Anna")

    def test_empty_house_is_more_important(self):
        empty = self._render("not_home", "not_home")
        occupied = self._render("home", "home")
        self.assertEqual(empty.value, "Leer")
        self.assertGreater(empty.importance, occupied.importance)

    def test_all_unavailable_hides_widget(self):
        hass = FakeHass({})
        widget = PresenceWidget(hass, entities=self.ENTITIES)
        self.assertIsNone(widget.render())


class FuelWidgetTest(unittest.TestCase):

    def _render(self, level, price, min_level=20.0, max_price=1.75):
        hass = FakeHass({
            "tank": FakeState(level),
            "preis": FakeState(price),
        })
        return FuelWidget(
            hass,
            level_entity="tank",
            price_entity="preis",
            min_level=min_level,
            max_price=max_price,
        ).render()

    def test_low_level_and_good_price_recommends(self):
        item = self._render("12", "1.65")
        self.assertEqual(item.value, "Tanken 1.65")
        self.assertEqual(item.icon, Icons.FUEL)
        self.assertEqual(item.importance, 85)

    def test_low_level_and_bad_price_shows_level(self):
        item = self._render("12", "1.95")
        self.assertEqual(item.value, "12%")

    def test_good_price_and_half_full_hints(self):
        item = self._render("35", "1.60")
        self.assertEqual(item.value, "1.60")
        self.assertEqual(item.importance, 40)

    def test_full_tank_and_bad_price_hidden(self):
        self.assertIsNone(self._render("90", "1.95"))

    def test_full_tank_and_good_price_hidden(self):
        self.assertIsNone(self._render("90", "1.60"))

    def test_liters_unit(self):
        hass = FakeHass({"tank": FakeState("10")})
        widget = FuelWidget(
            hass,
            level_entity="tank",
            price_entity="preis",
            min_level=15.0,
            unit="l",
        )
        self.assertEqual(widget.render().value, "10L")

    def test_missing_sensors_hidden(self):
        hass = FakeHass({})
        widget = FuelWidget(
            hass, level_entity="tank", price_entity="preis"
        )
        self.assertIsNone(widget.render())

    def test_level_only_works_without_price(self):
        hass = FakeHass({"tank": FakeState("10")})
        widget = FuelWidget(
            hass, level_entity="tank", price_entity="preis"
        )
        self.assertEqual(widget.render().value, "10%")


class DynamicFuelThresholdTest(unittest.TestCase):
    """max_price_entity: the threshold follows a reference sensor."""

    def _render(self, level, price, reference, margin=0.03):
        states = {
            "tank": FakeState(level),
            "preis": FakeState(price),
        }
        if reference is not None:
            states["tief"] = FakeState(reference)

        return FuelWidget(
            FakeHass(states),
            level_entity="tank",
            price_entity="preis",
            min_level=20.0,
            max_price=1.75,
            max_price_entity="tief",
            price_margin=margin,
        ).render()

    def test_price_within_margin_of_reference_is_good(self):
        # real values: 7-day low 1.979, price 1.989, tank 12 %
        item = self._render("12", "1.989", "1.979")
        self.assertEqual(item.value, "Tanken 1.99")
        self.assertEqual(item.importance, 85)

    def test_price_exactly_at_threshold_is_good(self):
        # 1.979 + 0.03 must not fail on float rounding
        item = self._render("12", "2.009", "1.979")
        self.assertEqual(item.value, "Tanken 2.01")

    def test_price_above_margin_is_not_good(self):
        item = self._render("12", "2.289", "1.979")
        self.assertEqual(item.value, "12%")

    def test_fixed_max_price_is_ignored_while_reference_exists(self):
        # 1.989 is far above the fixed 1.75 but good by reference
        item = self._render("12", "1.989", "1.979")
        self.assertTrue(item.value.startswith("Tanken"))

    def test_falls_back_to_fixed_price_without_reference_value(self):
        for reference in (None, "unknown", "unavailable"):
            item = self._render("12", "1.989", reference)
            self.assertEqual(item.value, "12%", reference)

    def test_fallback_still_recommends_below_fixed_price(self):
        item = self._render("12", "1.70", "unknown")
        self.assertEqual(item.value, "Tanken 1.70")

    def test_hint_for_half_empty_tank_at_good_price(self):
        # real values today: tank 26 %, price 1.989, low 1.979
        item = self._render("26", "1.989", "1.979")
        self.assertEqual(item.value, "1.99")
        self.assertEqual(item.importance, 40)

    def test_reference_entity_is_watched_by_the_updater(self):
        from custom_components.switchbot_dashboard.config.schema import (
            build_widget_configs,
        )
        from custom_components.switchbot_dashboard.updater import (
            collect_entities,
        )

        configs = build_widget_configs([{
            "type": "fuel",
            "level_entity": "sensor.tank",
            "price_entity": "sensor.preis",
            "max_price_entity": "sensor.tief",
            "price_margin": 0.03,
        }])
        self.assertEqual(configs[0].price_margin, 0.03)
        self.assertIn("sensor.tief", collect_entities(configs))


class RendererShorteningTest(unittest.TestCase):

    def test_render_caps_value_length(self):
        from custom_components.switchbot_dashboard.dashboard import (
            DashboardRenderer,
        )
        from custom_components.switchbot_dashboard.dashboard.item import (
            DashboardItem,
        )

        renderer = DashboardRenderer()
        renderer.add(
            DashboardItem("X", "Ein viel zu langer Widgettext", importance=50)
        )

        self.assertEqual(renderer.render(), "X Ein viel zu l…")


if __name__ == "__main__":
    unittest.main()
