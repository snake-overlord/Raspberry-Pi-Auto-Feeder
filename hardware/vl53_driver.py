class DistanceSensor:
    def __init__(self, sensor):
        self.sensor = sensor
        self.offset_mm = 0

    def set_offset(self, offset_mm):
        self.offset_mm = offset_mm

    def read_raw(self):
        return self.sensor.range

    def read_mm(self):
        return (self.sensor.range - self.offset_mm)

    def read_cm(self):
        return self.read_mm()/10

    