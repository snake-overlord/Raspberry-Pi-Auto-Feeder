from pathlib import Path

from fsm.feeder_fsm import FeederFSM
from services.logger import FileLogger
from services.telegram import TelegramCommands


class FakeBowl:
    def __init__(self, present=True, food=0, bowl_weight=100):
        self.present = present
        self.food = food
        self.bowl_weight = bowl_weight

    def is_present(self):
        return self.present

    def is_empty(self):
        return self.food <= 0

    def food_weight(self):
        return self.food

    def calibrate(self):
        self.bowl_weight = 123


class FakeHopper:
    def __init__(self, low=False):
        self.low = low

    def low_food(self):
        return self.low


class FakeDispenser:
    def __init__(self, bowl, portion_step=15):
        self.bowl = bowl
        self.portion_step = portion_step
        self.last_portion = 0
        self.daily_portion = 0

    def give_portion(self):
        self.bowl.food += self.portion_step
        self.last_portion = self.portion_step
        self.daily_portion += self.portion_step
        return self.portion_step

    def give_until(self, target_weight, tolerance=1, max_steps=10):
        portion = max(0, target_weight - self.bowl.food)
        self.bowl.food = target_weight
        self.last_portion = portion
        self.daily_portion += portion
        return portion

    def unjam(self):
        pass


class FakeTelegram:
    def __init__(self, chat_id=1):
        self.chat_id = chat_id
        self.sent = []
        self.updates = []

    def send(self, text, chat_id=None):
        self.sent.append((self.chat_id if chat_id is None else chat_id, text))
        return True

    def get_updates(self, offset=None, timeout=0):
        return self.updates


def make_commands():
    bowl = FakeBowl(present=True, food=10)
    hopper = FakeHopper(low=False)
    dispenser = FakeDispenser(bowl, portion_step=20)
    telegram = FakeTelegram(chat_id=10)
    fsm = FeederFSM(bowl, hopper, dispenser, telegram)
    commands = TelegramCommands(telegram, fsm, bowl, hopper, dispenser)
    return bowl, hopper, dispenser, telegram, fsm, commands


def test_help_command():
    bowl, hopper, dispenser, telegram, fsm, commands = make_commands()

    reply = commands.handle_text('/help')

    assert '/feed - выдать обычную порцию' in reply
    assert '/status - показать состояние' in reply


def test_feed_command():
    bowl, hopper, dispenser, telegram, fsm, commands = make_commands()

    reply = commands.handle_text('/feed')

    assert reply == 'Запущена выдача обычной порции'
    assert bowl.food == 30
    assert fsm.state == 'IDLE'


def test_feed_command_target():
    bowl, hopper, dispenser, telegram, fsm, commands = make_commands()

    reply = commands.handle_text('/feed 40')

    assert reply == 'Запущена выдача корма до 40.0 г'
    assert bowl.food == 40
    assert fsm.state == 'IDLE'


def test_status_command():
    bowl, hopper, dispenser, telegram, fsm, commands = make_commands()
    dispenser.last_portion = 12
    dispenser.daily_portion = 30

    reply = commands.handle_text('/status')

    assert 'Состояние:' in reply
    assert 'Миска на месте: да' in reply
    assert 'Еды в миске: 10.0 г' in reply
    assert 'За день: 30.0 г' in reply


def test_reset_command():
    bowl, hopper, dispenser, telegram, fsm, commands = make_commands()
    bowl.present = False
    fsm.feed()
    assert fsm.state == 'ERROR'

    reply = commands.handle_text('/reset')

    assert reply == 'Ошибка сброшена'
    assert fsm.state == 'IDLE'


def test_calibrate_command():
    bowl, hopper, dispenser, telegram, fsm, commands = make_commands()

    reply = commands.handle_text('/calibrate')

    assert bowl.bowl_weight == 123
    assert 'Миска откалибрована' in reply


def test_poll_reply():
    bowl, hopper, dispenser, telegram, fsm, commands = make_commands()
    telegram.updates = [
        {
            'update_id': 1,
            'message': {
                'text': '/status',
                'chat': {'id': 10}
            }
        }
    ]

    commands.poll_once()

    assert telegram.sent[-1][0] == 10
    assert 'Состояние:' in telegram.sent[-1][1]


def test_file_logger(tmp_path):
    log_path = tmp_path / 'feeder.log'
    logger = FileLogger(log_path)

    logger.log('тестовая запись')

    text = log_path.read_text(encoding='utf-8')
    assert 'тестовая запись' in text
