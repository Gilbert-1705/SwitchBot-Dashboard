"""Settings of the integration, from YAML and from the options flow.

One place that turns the ``switchbot_dashboard:`` block of
configuration.yaml into validated settings - used at start-up and by
the ``switchbot_dashboard.reload`` service, so a changed
configuration takes effect without restarting Home Assistant.

Free of Home Assistant imports on purpose: everything here is plain
data and can be tested without a running instance.
"""

from dataclasses import dataclass, replace

from .config.schema import ConfigError, build_widget_configs
from .const import (
    CONF_AUTO_REFRESH,
    CONF_DEVICE_ID,
    CONF_DRY_RUN,
    CONF_FIT_DISPLAY,
    CONF_MAX_ITEMS,
    CONF_QUIET_MAX_ITEMS,
    CONF_SECRET,
    CONF_TOKEN,
    CONF_WIDGETS,
    MAX_ITEMS,
    QUIET_MAX_ITEMS,
)
from .i18n import DEFAULT_LANGUAGE, LANGUAGES

CONF_LANGUAGE = "language"

CREDENTIAL_KEYS = (CONF_TOKEN, CONF_SECRET, CONF_DEVICE_ID)

# options a user may change at runtime (YAML and options flow)
OPTION_KEYS = (
    CONF_MAX_ITEMS,
    CONF_QUIET_MAX_ITEMS,
    CONF_AUTO_REFRESH,
    CONF_DRY_RUN,
    CONF_LANGUAGE,
    CONF_FIT_DISPLAY,
)

ALLOWED_KEYS = CREDENTIAL_KEYS + (CONF_WIDGETS,) + OPTION_KEYS

MAX_SLOTS = 10


@dataclass(slots=True)
class Settings:
    # None: use the Python fallback configuration (widgets/config.py)
    widgets: list | None = None
    max_items: int = MAX_ITEMS
    quiet_max_items: int = QUIET_MAX_ITEMS
    auto_refresh: bool = True
    dry_run: bool = False
    language: str = DEFAULT_LANGUAGE
    fit_display: bool = True


def settings_from_yaml(conf) -> Settings:
    """Validates the YAML block. Raises ConfigError with a clear text."""

    if not isinstance(conf, dict):
        raise ConfigError("expected a mapping under 'switchbot_dashboard:'")

    for key in conf:
        if key not in ALLOWED_KEYS:
            raise ConfigError(
                f"unknown option '{key}'. "
                f"Available: {', '.join(sorted(ALLOWED_KEYS))}"
            )

    widgets = None

    if conf.get(CONF_WIDGETS) is not None:
        widgets = build_widget_configs(conf[CONF_WIDGETS])

    return with_options(Settings(widgets=widgets), conf)


def with_options(settings: Settings, options) -> Settings:
    """Returns ``settings`` with the given options applied.

    ``options`` is the YAML block or the options of a config entry;
    keys that are not options are ignored.
    """

    changes = {}

    for key in OPTION_KEYS:
        if options is not None and key in options:
            changes[key] = _validate(key, options[key])

    return replace(settings, **changes)


def credentials_from(conf):
    """(token, secret, device_id) from the YAML block, or None.

    None means: the credentials come from a config entry (UI setup).
    Giving only some of them is an error.
    """

    present = [key for key in CREDENTIAL_KEYS if conf.get(key)]

    if not present:
        return None

    missing = [key for key in CREDENTIAL_KEYS if key not in present]

    if missing:
        raise ConfigError(
            f"incomplete credentials: missing {', '.join(missing)}"
        )

    return tuple(str(conf[key]) for key in CREDENTIAL_KEYS)


def _validate(key: str, value):

    if key in (CONF_MAX_ITEMS, CONF_QUIET_MAX_ITEMS):
        # bool is an int in Python - "max_items: true" is a mistake
        if isinstance(value, bool):
            raise ConfigError(f"'{key}' must be a number (got '{value}')")
        try:
            number = int(value)
        except (TypeError, ValueError):
            raise ConfigError(f"'{key}' must be a number (got '{value}')")
        if not 1 <= number <= MAX_SLOTS:
            raise ConfigError(
                f"'{key}' must be between 1 and {MAX_SLOTS} (got {number})"
            )
        return number

    if key in (CONF_AUTO_REFRESH, CONF_DRY_RUN, CONF_FIT_DISPLAY):
        if not isinstance(value, bool):
            raise ConfigError(
                f"'{key}' must be true or false (got '{value}')"
            )
        return value

    if key == CONF_LANGUAGE:
        if value not in LANGUAGES:
            raise ConfigError(
                f"'{key}' must be one of {', '.join(LANGUAGES)} "
                f"(got '{value}')"
            )
        return value

    return value
