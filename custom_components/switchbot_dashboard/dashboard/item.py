from dataclasses import dataclass


@dataclass(slots=True)
class DashboardItem:
    icon: str
    value: str

    priority: int = 100

    visible: bool = True