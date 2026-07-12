from .base import BaseFormatter


class NumberFormatter(BaseFormatter):

    def __init__(self, suffix=""):
        self.suffix = suffix

    def format(self, value):

        try:
            value = float(value)
        except (ValueError, TypeError):
            return "?"

        if value.is_integer():
            value = int(value)

        return f"{value}{self.suffix}"