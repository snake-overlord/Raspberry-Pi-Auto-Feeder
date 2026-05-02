import os
from datetime import date
from time import sleep
from domain.bowl import Bowl
from domain.dispenser import Dispenser
from fsm.feeder_fsm import FeederFSM
from domain.hopper import Hopper
from hardware.hx711_driver import HX711Driver
from services.logger import FileLogger
from domain.schedule import FeedingSchedule
from hardware.servo_driver import ServoDriver
from services.telegram import TelegramCommands, TelegramMessage
from hardware.vl53_driver import DistanceSensor


def load_env(path='.env'):
    if not os.path.exists(path):
        return

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def env_required(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f'Не задана переменная окружения {name}. '
            f'Создай .env по примеру из .env.example'
        )
    return value


def env_float(name, default):
    value = os.getenv(name)
    if value is None or value == '':
        return float(default)
    return float(value.replace(',', '.'))


def env_int(name, default):
    value = os.getenv(name)
    if value is None or value == '':
        return int(default)
    return int(value)


def create_logger():
    return FileLogger(os.getenv('FEEDER_LOG_PATH', 'feeder.log'))


def create_schedule():
    times_text = os.getenv('FEEDER_TIMES', '08:00,20:00')
    times = [item.strip() for item in times_text.split(',') if item.strip()]
    return FeedingSchedule(times)


def create_telegram():
    token = env_required('FEEDER_BOT_TOKEN')
    chat_id = int(env_required('FEEDER_CHAT_ID'))
    return TelegramMessage(chat_id, token)


def create_components(logger):
    try:
        from hardware_setup import create_servo, create_distance_sensor, create_weight_sensor
    except ImportError as e:
        raise RuntimeError('Ошибка импорта аппаратных компонентов.') from e

    bowl_sensor = HX711Driver(create_weight_sensor())
    bowl = Bowl(
        bowl_sensor,
        bowl_empty=env_float('FEEDER_BOWL_EMPTY', 100),
        empty_threshold=env_float('FEEDER_EMPTY_THRESHOLD', 0),
    )

    hopper_sensor = DistanceSensor(create_distance_sensor())
    hopper = Hopper(
        hopper_sensor,
        low_threshold_cm=env_float('FEEDER_HOPPER_LOW_CM', 19),
    )

    servo = ServoDriver(create_servo())
    dispenser = Dispenser(
        servo,
        bowl,
        portion=env_float('FEEDER_PORTION', 30),
    )

    telegram = create_telegram()
    fsm = FeederFSM(bowl, hopper, dispenser, telegram, logger=logger)
    schedule = create_schedule()
    commands = TelegramCommands(
        telegram,
        fsm,
        bowl,
        hopper,
        dispenser,
        schedule=schedule,
        logger=logger,
    )

    return bowl, hopper, dispenser, telegram, fsm, schedule, commands, servo


class FeederApp:
    def __init__(self):
        load_env()
        self.loop_sleep = env_float('FEEDER_LOOP_SLEEP', 0.5)
        self.telegram_timeout = env_int('FEEDER_TELEGRAM_TIMEOUT', 0)
        self.logger = create_logger()
        (
            self.bowl,
            self.hopper,
            self.dispenser,
            self.telegram,
            self.fsm,
            self.schedule,
            self.commands,
            self.servo,
        ) = create_components(self.logger)
        self.current_day = date.today()

    def log(self, text):
        self.logger.log(text)

    def reset_daily_if_needed(self):
        today = date.today()
        if today != self.current_day:
            self.dispenser.reset_daily()
            self.current_day = today
            self.log('Суточная статистика сброшена')

    def startup(self):
        self.log('Запуск автокормушки')
        self.servo.stop()
        self.fsm.start()
        self.telegram.send('Автокормушка запущена')

    def shutdown(self):
        try:
            self.servo.stop()
        except Exception:
            pass
        self.log('Остановка автокормушки')
        try:
            self.telegram.send('Автокормушка остановлена')
        except Exception:
            pass

    def step(self):
        self.commands.poll_once(timeout=self.telegram_timeout)

        if self.schedule.feed_now():
            self.log('Сработало расписание кормления')
            self.fsm.feed()

        self.reset_daily_if_needed()
        sleep(self.loop_sleep)

    def run(self):
        self.startup()
        try:
            while True:
                self.step()
        except KeyboardInterrupt:
            self.log('Получен KeyboardInterrupt')
        finally:
            self.shutdown()


if __name__ == '__main__':
    app = FeederApp()
    app.run()
