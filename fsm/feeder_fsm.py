from transitions import Machine

messages = {
    "IDLE": "Ожидание...",
    "DISPENSE": "Выдача корма...",
    "VERIFY": "Проверка...",
    "ERROR": "Ошибка",
    "RETRY": "Повторная попытка..."
}


class FeederFSM:
    states = [
        'BOOT',
        'IDLE',
        'CHECK_BOWL',
        'CHECK_HOPPER',
        'DISPENSE',
        'VERIFY',
        'ERROR',
        'RETRY'
    ]

    def __init__(self, bowl, hopper, dispenser, telegram, logger=None):
        self.bowl = bowl
        self.hopper = hopper
        self.dispenser = dispenser
        self.telegram = telegram
        self.logger = logger

        self.retry_count = 0
        self.max_retries = 3
        self.last_state = None
        self.target_weight = None
        self.error_message = None

        self.machine = Machine(
            model=self,
            states=FeederFSM.states,
            initial='BOOT',
            auto_transitions=False
        )

        self.machine.add_transition('start', 'BOOT', 'IDLE')
        self.machine.add_transition('feed_request', 'IDLE', 'CHECK_BOWL')
        self.machine.add_transition('fail', '*', 'ERROR')

        self.machine.add_transition(
            'check_ok',
            'CHECK_BOWL',
            'CHECK_HOPPER',
            conditions=['bowl_ok']
        )
        self.machine.add_transition(
            'check_ok',
            'CHECK_BOWL',
            'ERROR',
            unless=['bowl_ok']
        )

        self.machine.add_transition(
            'check_ok',
            'CHECK_HOPPER',
            'DISPENSE',
            conditions=['hopper_ok']
        )
        self.machine.add_transition(
            'check_ok',
            'CHECK_HOPPER',
            'ERROR',
            unless=['hopper_ok']
        )

        self.machine.add_transition('dispense_done', 'DISPENSE', 'VERIFY')

        self.machine.add_transition(
            'verify_done',
            'VERIFY',
            'IDLE',
            conditions=['verify_ok']
        )
        self.machine.add_transition(
            'verify_done',
            'VERIFY',
            'RETRY',
            unless=['verify_ok']
        )

        self.machine.add_transition(
            'retry',
            'RETRY',
            'DISPENSE',
            conditions=['can_retry'],
            before='do_retry'
        )
        self.machine.add_transition(
            'retry',
            'RETRY',
            'ERROR',
            unless=['can_retry']
        )

        self.machine.add_transition('reset', 'ERROR', 'IDLE')

    def log(self, text):
        if self.logger:
            self.logger.log(text)

    def feed(self, target_weight=None):
        if self.state == 'BOOT':
            self.start()

        if self.state == 'ERROR':
            self.reset()

        self.target_weight = target_weight
        self.error_message = None

        if target_weight is None:
            self.log('Запрос на выдачу обычной порции')
        else:
            self.log(f'Запрос на выдачу до {target_weight} г')

        if self.state == 'IDLE':
            self.feed_request()

    # conditions

    def bowl_ok(self):
        return self.bowl.is_present()

    def hopper_ok(self):
        return not self.hopper.low_food()

    def verify_ok(self):
        if self.target_weight is not None:
            return self.bowl.food_weight() >= self.target_weight
        return not self.bowl.is_empty()

    def can_retry(self):
        return self.retry_count < self.max_retries

    def notify(self):
        if self.state != self.last_state:
            msg = messages.get(self.state, self.state)
            if self.telegram:
                self.telegram.send(msg)
            self.log(f'Состояние: {self.state}')
            self.last_state = self.state

    # callbacks

    def on_enter_CHECK_BOWL(self):
        self.notify()
        if not self.bowl_ok():
            self.error_message = 'Миска не обнаружена'
            self.log(self.error_message)
        self.check_ok()

    def on_enter_CHECK_HOPPER(self):
        self.notify()
        if not self.hopper_ok():
            self.error_message = 'В бункере мало корма'
            self.log(self.error_message)
        self.check_ok()

    def on_enter_DISPENSE(self):
        self.notify()

        try:
            if self.target_weight is not None:
                portion = self.dispenser.give_until(self.target_weight)
            else:
                portion = self.dispenser.give_portion()
        except Exception as e:
            self.error_message = f'Ошибка выдачи корма: {e}'
            self.log(self.error_message)
            self.fail()
            return

        self.log(f'Выдано {portion:.1f} г')

        if self.telegram:
            self.telegram.send(f'Выдано {portion:.1f} г')

        self.dispense_done()

    def on_enter_VERIFY(self):
        self.notify()
        if not self.verify_ok() and self.target_weight is not None:
            self.log(f'Недостаточно корма в миске: {self.bowl.food_weight():.1f} г из {self.target_weight} г')
        elif not self.verify_ok():
            self.log('Корм не появился в миске, нужна повторная попытка')
        self.verify_done()

    def on_enter_RETRY(self):
        self.notify()
        self.dispenser.unjam()
        self.log(f'Повторная попытка #{self.retry_count + 1}')

        if not self.can_retry():
            if self.target_weight is not None:
                self.error_message = (
                    f'Не удалось досыпать до {self.target_weight} г, '
                    f'сейчас {self.bowl.food_weight():.1f} г'
                )
            else:
                self.error_message = 'Не удалось выдать корм после нескольких попыток'
            self.log(self.error_message)

        self.retry()

    def do_retry(self):
        self.retry_count += 1

    def on_enter_IDLE(self):
        self.notify()
        self.retry_count = 0
        self.target_weight = None
        self.log('Цикл кормления завершен')

    def on_enter_ERROR(self):
        self.notify()
        self.log(self.error_message or 'Неизвестная ошибка')
        if self.telegram and self.error_message:
            self.telegram.send(self.error_message)
