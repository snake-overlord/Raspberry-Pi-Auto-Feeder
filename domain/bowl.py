class Bowl:
    def __init__(self, sensor, bowl_empty=100, empty_threshold=5):
        self.sensor = sensor
        self.bowl_weight = bowl_empty
        self.empty_threshold = empty_threshold

    def is_empty(self):
        return self.food_weight() <= self.empty_threshold

    def is_present(self):
        return self.total_weight() > self.bowl_weight * 0.5

    def calibrate(self):
        self.bowl_weight = self.sensor.read()

    def food_weight(self):
        return max(0, self.total_weight() - self.bowl_weight)

    def total_weight(self):
        return self.sensor.read()
