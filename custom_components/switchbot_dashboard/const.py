DOMAIN = "switchbot_dashboard"

CONF_TOKEN = "token"
CONF_SECRET = "secret"
CONF_DEVICE_ID = "device_id"
CONF_WIDGETS = "widgets"
CONF_MAX_ITEMS = "max_items"

API_URL = "https://api.switch-bot.com/v1.1/devices/{device_id}/commands"

# Maximale Anzahl gleichzeitig angezeigter Widgets
MAX_ITEMS = 5

# Sicherheitsgrenze pro Widget-Text (Display bricht pixelbasiert um)
MAX_VALUE_LENGTH = 14

# Trenner zwischen Widgets - drei Leerzeichen nutzt die
# SwitchBot-Firmware als bevorzugte Umbruchstelle
SEPARATOR = "   "