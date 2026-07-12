from .base import BaseFormatter


class PowerFormatter(BaseFormatter):

    def format(self, value):

        try:
            value = float(value)
        except (ValueError, TypeError):
            return "?"

        value = abs(value)

        if value < 1000:
            return f"{value:.0f}W"

        if value < 10000:
            return f"{value / 1000:.1f}kW"

        return f"{value / 1000:.0f}kW"