import re

from .base import BaseWidget, DashboardItem
from ..icons import Icons

PLAYING_STATES = ("playing",)

# trailing additions that cost space and say little:
# "Song (Remastered 2011)", "Song - Radio Edit", "Song [Live]"
_SUFFIX = re.compile(r"\s*(\(.*\)|\[.*\]|\s-\s.*)$")


class MediaWidget(BaseWidget):
    """What is playing right now.

        ♪ Bohemian Rhapsody     title (default)
        ♪ Queen                 show: artist
        ♪ Queen: Bohemian Rh…   show: both
        (nothing)               paused, idle, off

    With several players the first one that is playing wins, in the
    configured order. The display is only updated when the text
    changes - a new title, not the running position.
    """

    def __init__(
        self,
        hass,
        entity: str = "",
        entities: list | None = None,
        icon: str = Icons.MUSIC,
        show: str = "title",
        max_length: int = 20,
        importance: int = 30,
        priority: int = 900,
    ):
        super().__init__(hass)

        self.entities = ([entity] if entity else []) + list(entities or [])
        self.icon = icon
        self.show = show
        self.max_length = max_length
        self.importance = importance
        self.priority = priority

    def render(self):

        for entity in self.entities:

            state = self.hass.states.get(entity)

            if state is None:
                continue

            if str(state.state).lower() not in PLAYING_STATES:
                continue

            text = self._text(state.attributes or {})

            if text:
                return DashboardItem(
                    icon=self.icon,
                    value=text,
                    priority=self.priority,
                    importance=self.importance,
                    max_length=self.max_length,
                )

        return None

    def _text(self, attributes) -> str:

        title = _clean(attributes.get("media_title"))

        # AirPlay receivers report their app ID as the title
        # ("com.apple.tvairplayd") when they do not know the song
        if title and title == _clean(attributes.get("app_id")):
            title = ""
        artist = _clean(
            attributes.get("media_artist")
            or attributes.get("media_album_artist")
        )

        if self.show == "artist":
            return artist or title

        if self.show == "both" and artist and title:
            return f"{artist}: {self._compact(title)}"

        return self._compact(title) or artist

    def _compact(self, title: str) -> str:
        """Drops additions like "(Remastered)" when space is short."""

        while len(title) > self.max_length:
            shorter = _SUFFIX.sub("", title).strip()

            if not shorter or shorter == title:
                break

            title = shorter

        return title


def _clean(value) -> str:

    if value is None:
        return ""

    return " ".join(str(value).split())
