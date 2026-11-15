"""Tests for the media widget.

Run (from the repo root):

    python3 custom_components/switchbot_dashboard/tests/test_media.py
"""

import unittest

import helpers  # noqa: F401  (stubs HA/aiohttp, sets sys.path)
from helpers import FakeHass, FakeState

from custom_components.switchbot_dashboard.config.schema import (
    ConfigError,
    build_widget_configs,
)
from custom_components.switchbot_dashboard.render import render_dashboard
from custom_components.switchbot_dashboard.updater import collect_entities
from custom_components.switchbot_dashboard.widgets.media import MediaWidget


def playing(title="Bohemian Rhapsody", artist="Queen", state="playing"):
    return FakeState(
        state, {"media_title": title, "media_artist": artist}
    )


class MediaWidgetTest(unittest.TestCase):

    def _render(self, state, **kwargs):
        return MediaWidget(
            FakeHass({"player": state}), entity="player", **kwargs
        ).render()

    def test_shows_the_title_while_playing(self):
        item = self._render(playing())
        self.assertEqual(item.icon, "♪")
        self.assertEqual(item.value, "Bohemian Rhapsody")
        self.assertEqual(item.importance, 30)
        self.assertEqual(item.max_length, 20)

    def test_hidden_when_not_playing(self):
        for state in ("paused", "idle", "off", "unavailable", "standby"):
            self.assertIsNone(self._render(playing(state=state)), state)

    def test_hidden_when_the_player_is_missing(self):
        widget = MediaWidget(FakeHass({}), entity="player")
        self.assertIsNone(widget.render())

    def test_hidden_without_any_text(self):
        self.assertIsNone(self._render(FakeState("playing", {})))

    def test_artist_only(self):
        item = self._render(playing(), show="artist")
        self.assertEqual(item.value, "Queen")

    def test_both(self):
        item = self._render(playing("Yesterday", "Beatles"), show="both")
        self.assertEqual(item.value, "Beatles: Yesterday")

    def test_title_falls_back_to_artist(self):
        item = self._render(playing(title=None))
        self.assertEqual(item.value, "Queen")

    def test_long_title_loses_its_additions(self):
        item = self._render(
            playing("Under Pressure - Remastered 2011 (Live) [Bonus]")
        )
        self.assertEqual(item.value, "Under Pressure")

    def test_short_title_keeps_its_additions(self):
        item = self._render(playing("Help! (Live)"))
        self.assertEqual(item.value, "Help! (Live)")

    def test_title_that_is_only_an_addition_survives(self):
        item = self._render(playing("(I Can't Get No) Satisfaction, yes"))
        self.assertTrue(item.value)

    def test_app_id_is_not_a_title(self):
        state = FakeState("playing", {
            "media_title": "com.apple.tvairplayd",
            "app_id": "com.apple.tvairplayd",
        })
        self.assertIsNone(self._render(state))

    def test_whitespace_is_collapsed(self):
        item = self._render(playing("  Hey \n Jude "))
        self.assertEqual(item.value, "Hey Jude")

    def test_first_playing_player_wins(self):
        hass = FakeHass({
            "a": playing("A", state="paused"),
            "b": playing("B"),
            "c": playing("C"),
        })
        item = MediaWidget(hass, entities=["a", "b", "c"]).render()
        self.assertEqual(item.value, "B")


class MediaPipelineTest(unittest.TestCase):

    def test_long_titles_get_more_room_than_other_widgets(self):
        configs = build_widget_configs([
            {"type": "media", "entity": "player"},
        ])
        hass = FakeHass({
            "player": playing("A Very Long Title That Never Ends"),
        })
        self.assertEqual(
            render_dashboard(hass, configs), "♪ A Very Long Title T…"
        )

    def test_max_length_is_configurable(self):
        configs = build_widget_configs([
            {"type": "media", "entity": "player", "max_length": 12},
        ])
        hass = FakeHass({"player": playing("Bohemian Rhapsody")})
        self.assertEqual(render_dashboard(hass, configs), "♪ Bohemian Rh…")

    def test_needs_a_player(self):
        with self.assertRaises(ConfigError):
            build_widget_configs([{"type": "media"}])

    def test_show_is_validated(self):
        with self.assertRaises(ConfigError):
            build_widget_configs(
                [{"type": "media", "entity": "p", "show": "album"}]
            )

    def test_entities_must_be_a_list(self):
        with self.assertRaises(ConfigError):
            build_widget_configs(
                [{"type": "media", "entities": "media_player.a"}]
            )

    def test_all_players_are_watched(self):
        configs = build_widget_configs([
            {"type": "media", "entity": "media_player.a",
             "entities": ["media_player.b", "media_player.c"]},
            {"type": "status", "entities": {"binary_sensor.nas": "NAS"}},
        ])
        self.assertEqual(
            collect_entities(configs),
            {"media_player.a", "media_player.b", "media_player.c",
             "binary_sensor.nas"},
        )


if __name__ == "__main__":
    unittest.main()
