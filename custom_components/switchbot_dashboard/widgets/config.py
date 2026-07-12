from ..config.entities import Entities
from ..icons import Icons
from .config_models import (
    CalendarWidgetConfig,
    EntityWidgetConfig,
    FuelWidgetConfig,
    PresenceWidgetConfig,
    WidgetConfig,
    WindowWidgetConfig,
)

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
        entities={
            Entities.WINDOW_1: "Wohnen",
            Entities.WINDOW_2: "Essen",
        },
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
    CalendarWidgetConfig(
        type="calendar",
        entity=Entities.CALENDAR_BIRTHDAYS,
        icon=Icons.BIRTHDAY,
        days=1,
        priority=500,
    ),
    CalendarWidgetConfig(
        type="calendar",
        entity=Entities.CALENDAR_APPOINTMENTS,
        icon=Icons.CALENDAR,
        days=1,
        priority=510,
    ),
    CalendarWidgetConfig(
        type="calendar",
        entity=Entities.CALENDAR_HOLIDAYS,
        icon=Icons.HOLIDAY,
        days=1,
        priority=520,
    ),
    CalendarWidgetConfig(
        type="calendar",
        entity=Entities.CALENDAR_VACATION,
        icon=Icons.VACATION,
        days=3,
        priority=530,
    ),
    PresenceWidgetConfig(
        type="presence",
        entities={
            Entities.PERSON_1: "Jan",
            Entities.PERSON_2: "Anna",
        },
        priority=600,
    ),
    FuelWidgetConfig(
        type="fuel",
        level_entity=Entities.CAR_FUEL_LEVEL,
        price_entity=Entities.FUEL_PRICE,
        min_level=20.0,
        max_price=1.75,
        unit="%",
        priority=610,
    ),
]