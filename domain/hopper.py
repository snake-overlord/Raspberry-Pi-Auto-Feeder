from __future__ import annotations


class Hopper:
    def __init__(self, sensor, low_threshold_cm: float = 19.0):
        self.sensor = sensor
        self.low_threshold = float(low_threshold_cm)

    def level_cm(self) -> float:
        return float(self.sensor.read_cm())

    def low_food(self) -> bool:
        return self.level_cm() > self.low_threshold

    def has_food(self) -> bool:
        return not self.low_food()
