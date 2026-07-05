from ..config.entities import Entities
from ..icons import Icons
from .config_models import EntityWidgetConfig, WidgetConfig

WIDGETS = [
    {
        "type": "weather",
        "priority": 100,
    },
    {
        "type": "entity",
        "entity": Entities.POWER,
        "icon": Icons.POWER,
        "formatter": "power",
        "priority": 200,
    },
    {
        "type": "door",
        "priority": 300,
    },
]