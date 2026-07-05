from .base import BaseFormatter
from .power import PowerFormatter


class FormatterFactory:

    @staticmethod
    def create(name: str):

        if name == "power":
            return PowerFormatter()

        if name == "number":
            return NumberFormatter()

        return BaseFormatter()