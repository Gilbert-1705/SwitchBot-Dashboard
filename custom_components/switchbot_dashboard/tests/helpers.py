"""Gemeinsame Test-Helpers.

Stubbt Home Assistant und aiohttp, damit die Tests ohne
HA-Installation laufen, und stellt Fakes bereit. Der Import hat
Seiteneffekte (Stubs + sys.path) und muss VOR den Paket-Imports
stehen:

    import helpers  # noqa: F401
    from helpers import FakeHass, FakeState
"""

import sys
import types
from pathlib import Path

# Repo-Root auf den Pfad legen
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

if "homeassistant" not in sys.modules:
    ha = types.ModuleType("homeassistant")
    ha_core = types.ModuleType("homeassistant.core")
    ha_core.HomeAssistant = object
    ha_core.State = object
    ha_core.ServiceCall = object

    ha_const = types.ModuleType("homeassistant.const")
    ha_const.EVENT_HOMEASSISTANT_STARTED = "homeassistant_started"

    ha_helpers = types.ModuleType("homeassistant.helpers")
    ha_event = types.ModuleType("homeassistant.helpers.event")
    ha_event.async_call_later = lambda hass, delay, action: (lambda: None)
    ha_event.async_track_state_change_event = (
        lambda hass, entities, action: (lambda: None)
    )
    ha_event.async_track_time_interval = (
        lambda hass, action, interval: (lambda: None)
    )

    ha.core = ha_core
    ha.const = ha_const
    ha.helpers = ha_helpers
    ha_helpers.event = ha_event

    sys.modules["homeassistant"] = ha
    sys.modules["homeassistant.core"] = ha_core
    sys.modules["homeassistant.const"] = ha_const
    sys.modules["homeassistant.helpers"] = ha_helpers
    sys.modules["homeassistant.helpers.event"] = ha_event

if "aiohttp" not in sys.modules:
    aiohttp = types.ModuleType("aiohttp")
    aiohttp.ClientSession = object
    sys.modules["aiohttp"] = aiohttp


class FakeState:

    def __init__(self, state, attributes=None):
        self.state = state
        self.attributes = attributes or {}


class FakeHass:

    def __init__(self, states=None):
        # per async_set gesetzte States (z.B. Preview-Entity)
        self.set_states: dict = {}

        def async_set(entity_id, state, attributes=None):
            self.set_states[entity_id] = (state, attributes or {})

        self.states = types.SimpleNamespace(
            get=(states or {}).get,
            async_set=async_set,
        )
