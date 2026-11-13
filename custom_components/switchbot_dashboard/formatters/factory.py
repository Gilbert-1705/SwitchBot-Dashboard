from .base import BaseFormatter
from .power import PowerFormatter
from .number import NumberFormatter


class FormatterFactory:
    """Creates formatters by name.

    Custom formatters can be registered:

        FormatterFactory.register("euro", EuroFormatter)

    Afterwards ``formatter: euro`` is usable in the configuration.
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
