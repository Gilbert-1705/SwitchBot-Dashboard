from ..config.entities import Entities
from ..icons import Icons
from .config_models import EntityWidgetConfig, WidgetConfig, WindowWidgetConfig

WIDGETS = [
    WidgetConfig(
        type="weather",
        priority=100,
    ),
    EntityWidgetConfig(
        type="entity",
        entity=Entities.POWER,
        icon=Icons.POWER,
        formatter="power",
        priority=200,
    ),
    WindowWidgetConfig(
        type="window",
        entities=[
            Entities.WINDOW_1,
            Entities.WINDOW_2,
        ],
        priority=250,
    ),
    WidgetConfig(
        type="door",
        priority=300,
    ),
    WidgetConfig(
        type="waste",
        priority=400,
    ),
]