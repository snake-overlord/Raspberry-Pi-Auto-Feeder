from time import sleep


class ServoDriver:
    def __init__(self, servo):
        self.servo = servo
        self.max_runtime = 100.0
        self.stop()

    def _run(self, power):
        self.servo.value = power

    def stop(self):
        self.servo.value = 0

    def pulse(self, power, duration):
        self._run(power)
        try:
            sleep(min(duration, self.max_runtime))
        finally:
            self.stop()

    def jiggle(self):
        self.pulse(-0.8, 0.5)
        self.pulse(0.8, 0.5)
        self.stop()
