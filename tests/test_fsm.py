from fsm.feeder_fsm import FeederFSM


class FakeBowl:
    def __init__(self, present=True, food=0):
        self.present = present
        self.food = food

    def is_present(self):
        return self.present

    def is_empty(self):
        return self.food <= 0

    def food_weight(self):
        return self.food


class FakeHopper:
    def __init__(self, low=False):
        self.low = low

    def low_food(self):
        return self.low


class FakeDispenser:
    def __init__(self, bowl, portion_step=15, give_until_result=None):
        self.bowl = bowl
        self.portion_step = portion_step
        self.give_until_result = give_until_result
        self.give_portion_calls = 0
        self.give_until_calls = []
        self.unjam_calls = 0

    def give_portion(self):
        self.give_portion_calls += 1
        self.bowl.food += self.portion_step
        return self.portion_step

    def give_until(self, target_weight, tolerance=1, max_steps=10):
        self.give_until_calls.append(target_weight)
        if self.give_until_result is not None:
            self.bowl.food = self.give_until_result
        else:
            self.bowl.food = target_weight
        return self.bowl.food

    def unjam(self):
        self.unjam_calls += 1


class FakeTelegram:
    def __init__(self):
        self.messages = []

    def send(self, text):
        self.messages.append(text)


def test_fsm_success():
    bowl = FakeBowl(present=True, food=0)
    hopper = FakeHopper(low=False)
    dispenser = FakeDispenser(bowl, portion_step=20)
    telegram = FakeTelegram()
    fsm = FeederFSM(bowl, hopper, dispenser, telegram)

    fsm.feed()

    assert fsm.state == 'IDLE'
    assert bowl.food == 20
    assert dispenser.give_portion_calls == 1
    assert fsm.error_message is None
    assert 'Выдано 20.0 г' in telegram.messages


def test_fsm_bowl_missing():
    bowl = FakeBowl(present=False, food=0)
    hopper = FakeHopper(low=False)
    dispenser = FakeDispenser(bowl)
    telegram = FakeTelegram()
    fsm = FeederFSM(bowl, hopper, dispenser, telegram)

    fsm.feed()

    assert fsm.state == 'ERROR'
    assert fsm.error_message == 'Миска не обнаружена'
    assert dispenser.give_portion_calls == 0
    assert 'Миска не обнаружена' in telegram.messages


def test_fsm_hopper_low():
    bowl = FakeBowl(present=True, food=0)
    hopper = FakeHopper(low=True)
    dispenser = FakeDispenser(bowl)
    telegram = FakeTelegram()
    fsm = FeederFSM(bowl, hopper, dispenser, telegram)

    fsm.feed()

    assert fsm.state == 'ERROR'
    assert fsm.error_message == 'В бункере мало корма'
    assert dispenser.give_portion_calls == 0
    assert 'В бункере мало корма' in telegram.messages


def test_fsm_target_weight():
    bowl = FakeBowl(present=True, food=10)
    hopper = FakeHopper(low=False)
    dispenser = FakeDispenser(bowl, give_until_result=40)
    telegram = FakeTelegram()
    fsm = FeederFSM(bowl, hopper, dispenser, telegram)

    fsm.feed(target_weight=40)

    assert fsm.state == 'IDLE'
    assert bowl.food == 40
    assert dispenser.give_until_calls == [40]
    assert fsm.target_weight is None
    assert 'Выдано 40.0 г' in telegram.messages


def test_fsm_retry_fail():
    bowl = FakeBowl(present=True, food=0)
    hopper = FakeHopper(low=False)
    dispenser = FakeDispenser(bowl, portion_step=0)
    telegram = FakeTelegram()
    fsm = FeederFSM(bowl, hopper, dispenser, telegram)

    fsm.feed()

    assert fsm.state == 'ERROR'
    assert fsm.error_message == 'Не удалось выдать корм после нескольких попыток'
    assert dispenser.give_portion_calls == 4
    assert dispenser.unjam_calls == 4
    assert fsm.retry_count == 3
    assert 'Не удалось выдать корм после нескольких попыток' in telegram.messages


def test_fsm_after_error():
    bowl = FakeBowl(present=False, food=0)
    hopper = FakeHopper(low=False)
    dispenser = FakeDispenser(bowl, portion_step=10)
    telegram = FakeTelegram()
    fsm = FeederFSM(bowl, hopper, dispenser, telegram)

    fsm.feed()
    assert fsm.state == 'ERROR'

    bowl.present = True
    fsm.feed()

    assert fsm.state == 'IDLE'
    assert bowl.food == 10
