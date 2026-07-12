from .base import BaseFormatter
from .power import PowerFormatter
from .number import NumberFormatter


class FormatterFactory:
    """Erzeugt Formatter anhand ihres Namens.

    Eigene Formatter lassen sich registrieren:

        FormatterFactory.register("euro", EuroFormatter)

    Danach ist ``formatter: euro`` in der Konfiguration nutzbar.
    """

    _formatters: dict[str, type] = {
        "power": PowerFormatter,
        "number": NumberFormatter,
    }

    @classmethod
    def register(cls, name: str, formatter_cls: type):
        cls._formatters[name] = formatter_cls

    @classmethod
    def names(cls) -> list[str]:
        return sorted(cls._formatters)

    @classmethod
    def create(cls, name: str) -> BaseFormatter:

        formatter_cls = cls._formatters.get(name, BaseFormatter)

        return formatter_cls()
