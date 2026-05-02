class Dispenser:
    def __init__(self, servo, bowl, portion=30):
        self.servo = servo
        self.bowl = bowl
        self.portion = portion

        self.last_portion = 0
        self.daily_portion = 0

    def give_portion(self):
        before = self.bowl.food_weight()

        self.servo.pulse(0.5, 10)

        after = self.bowl.food_weight()
        portion = max(0, after - before)

        self.last_portion = portion
        self.daily_portion += portion

        return portion

    def give_until(self, target_weight, tolerance=1, max_steps=10):
        start = self.bowl.food_weight()
        current = start
        steps = 0

        while current + tolerance < target_weight and steps < max_steps:
            self.servo.pulse(0.5, 10)
            current = self.bowl.food_weight()
            steps += 1

        portion = max(0, current - start)
        self.last_portion = portion
        self.daily_portion += portion

        return portion

    def unjam(self):
        self.servo.jiggle()

    def reset_daily(self):
        self.daily_portion = 0
