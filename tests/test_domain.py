import domain.schedule as schedule
from domain.bowl import Bowl
from domain.dispenser import Dispenser
from domain.hopper import Hopper
from domain.schedule import FeedingSchedule


class FakeScale:
    def __init__(self, value=0):
        self.value = value

    def read(self):
        return self.value


class FakeDistanceSensor:
    def __init__(self, value_cm=0):
        self.value_cm = value_cm

    def read_cm(self):
        return self.value_cm


class FakeBowl:
    def __init__(self, food=0, step=0):
        self.food = food
        self.step = step

    def food_weight(self):
        return self.food


class FakeServo:
    def __init__(self, bowl=None, step=0):
        self.bowl = bowl
        self.step = step
        self.pulses = 0
        self.jiggles = 0

    def pulse(self, power, duration):
        self.pulses += 1
        if self.bowl:
            self.bowl.food += self.step

    def jiggle(self):
        self.jiggles += 1


class FakeDatetimeValue:
    def __init__(self, value):
        self.value = value

    def strftime(self, fmt):
        return self.value


class FakeDatetime:
    current = '00:00'

    @classmethod
    def now(cls):
        return FakeDatetimeValue(cls.current)


def test_bowl_empty_and_present():
    sensor = FakeScale(100)
    bowl = Bowl(sensor, bowl_empty=100, empty_threshold=0)

    assert bowl.is_empty() is True
    assert bowl.is_present() is True

    sensor.value = 40
    assert bowl.is_present() is False


def test_bowl_calibrate():
    sensor = FakeScale(135)
    bowl = Bowl(sensor, bowl_empty=100)

    bowl.calibrate()

    assert bowl.bowl_weight == 135


def test_dispenser_give_portion():
    bowl = FakeBowl(food=10)
    servo = FakeServo(bowl=bowl, step=15)
    dispenser = Dispenser(servo, bowl)

    portion = dispenser.give_portion()

    assert portion == 15
    assert dispenser.last_portion == 15
    assert dispenser.daily_portion == 15
    assert servo.pulses == 1


def test_dispenser_give_until():
    bowl = FakeBowl(food=10)
    servo = FakeServo(bowl=bowl, step=12)
    dispenser = Dispenser(servo, bowl)

    portion = dispenser.give_until(30)

    assert bowl.food == 34
    assert portion == 24
    assert dispenser.last_portion == 24
    assert dispenser.daily_portion == 24
    assert servo.pulses == 2


def test_hopper_low_food():
    sensor = FakeDistanceSensor(25)
    hopper = Hopper(sensor, low_threshold_cm=19)

    assert hopper.low_food() is True

    sensor.value_cm = 10
    assert hopper.low_food() is False


def test_schedule(monkeypatch):
    monkeypatch.setattr(schedule, 'datetime', FakeDatetime)
    feeding_schedule = FeedingSchedule(['08:00'])

    FakeDatetime.current = '08:00'
    assert feeding_schedule.feed_now() is True
    assert feeding_schedule.feed_now() is False

    FakeDatetime.current = '08:01'
    assert feeding_schedule.feed_now() is False
