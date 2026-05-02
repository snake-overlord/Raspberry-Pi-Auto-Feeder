class HX711Driver:
    def __init__(self, hx):
        self.hx = hx

    def read(self):
        return self.hx.get_grams()
    
    def set_offset(self, value):
        self.hx.set_offset(value)

    def set_scale(self, value):
        self.hx.set_scale(value)

    def tare(self):
        self.hx.tare()

