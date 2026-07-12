DOMAIN = "switchbot_dashboard"

CONF_TOKEN = "token"
CONF_SECRET = "secret"
CONF_DEVICE_ID = "device_id"
CONF_WIDGETS = "widgets"
CONF_MAX_ITEMS = "max_items"
CONF_AUTO_REFRESH = "auto_refresh"
CONF_DRY_RUN = "dry_run"

# Local preview entity: shows the currently rendered display line
PREVIEW_ENTITY_ID = "sensor.switchbot_dashboard"

API_URL = "https://api.switch-bot.com/v1.1/devices/{device_id}/commands"

# Maximum number of widgets shown at the same time
MAX_ITEMS = 5

# Safety cap per widget text (display wraps pixel-based)
MAX_VALUE_LENGTH = 14

# Hard API limit: the SwitchBot API rejects payloads over
# ~300 bytes (UTF-8) with statusCode 190
MAX_PAYLOAD_BYTES = 300

# Separator between widgets - the SwitchBot firmware uses three
# spaces as its preferred line-break position
SEPARATOR = "   "