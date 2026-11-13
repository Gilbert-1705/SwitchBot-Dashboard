from .base import BaseFormatter

# Below 1 kW the value is rounded to this step. A power meter reports
# a new value every few seconds; shown to the watt, the line would
# change (and the e-paper refresh) up to once a minute.
WATT_STEP = 10


class PowerFormatter(BaseFormatter):

    def format(self, value):

        try:
            value = float(value)
        except (ValueError, TypeError):
            return "?"

        value = abs(value)

        if value < 1000:
            rounded = round(value / WATT_STEP) * WATT_STEP
            # 996 W rounds up to the kW range
            if rounded < 1000:
                return f"{rounded:.0f}W"
            value = rounded

        if value < 10000:
            return f"{value / 1000:.1f}kW"

        return f"{value / 1000:.0f}kW"
