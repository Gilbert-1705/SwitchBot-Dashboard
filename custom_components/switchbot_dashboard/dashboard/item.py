from dataclasses import dataclass


@dataclass(slots=True)
class DashboardItem:
    """Ein renderbares Dashboard-Element.

    priority   -> Anzeigereihenfolge (kleiner = weiter vorne)
    importance -> Wie wichtig ist die Information JETZT?
                  Das Dashboard zeigt nur die wichtigsten Items.

    Importance-Skala:
        100     Warnung, sofort handeln (z.B. abgeschlossen, aber offen)
        70-90   heute relevant (Müll heute, Geburtstag, Tür offen)
        40-60   demnächst relevant (Termin in 2 Tagen, Fenster offen)
        10-30   Hintergrundinformation (Stromverbrauch, alles zu)
    """

    icon: str
    value: str

    priority: int = 100

    importance: int = 0

    visible: bool = True
