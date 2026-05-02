import requests


class TelegramMessage:
    def __init__(self, chat_id, token):
        self.token = token
        self.chat_id = chat_id
        self.send_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        self.updates_url = f"https://api.telegram.org/bot{self.token}/getUpdates"

    def send(self, text, chat_id=None):
        target_chat = self.chat_id if chat_id is None else chat_id

        try:
            response = requests.post(self.send_url, json={
                "chat_id": target_chat,
                "text": text
            }, timeout=5)
            response.raise_for_status()
            return True
        except Exception as e:
            print("Telegram connection error:", e)
            return False

    def get_updates(self, offset=None, timeout=0):
        params = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset

        try:
            response = requests.get(self.updates_url, params=params, timeout=timeout + 5)
            response.raise_for_status()
            data = response.json()
            return data.get('result', [])
        except Exception as e:
            print("Telegram read error:", e)
            return []


class TelegramCommands:
    def __init__(self, telegram, fsm, bowl, hopper, dispenser, schedule=None, logger=None):
        self.telegram = telegram
        self.fsm = fsm
        self.bowl = bowl
        self.hopper = hopper
        self.dispenser = dispenser
        self.schedule = schedule
        self.logger = logger
        self.last_update_id = None

    def log(self, text):
        if self.logger:
            self.logger.log(text)

    def help_text(self):
        return (
            'Команды:\n'
            '/feed - выдать обычную порцию\n'
            '/feed 40 - выдать корм до 40г в миске\n'
            '/status - показать состояние\n'
            '/reset - сбросить\n'
            '/calibrate - откалибровать пустую миску\n'
            '/daily - показать статистику за день\n'
            '/help - показать команды'
        )

    def status_text(self):
        lines = [f'Состояние: {self.fsm.state}']

        try:
            lines.append(f'Миска на месте: {"да" if self.bowl.is_present() else "нет"}')
        except Exception:
            lines.append('Миска на месте: ошибка чтения')

        try:
            lines.append(f'Еды в миске: {self.bowl.food_weight():.1f} г')
        except Exception:
            lines.append('Еды в миске: ошибка чтения')

        try:
            lines.append(f'Корм в бункере: {"мало" if self.hopper.low_food() else "норма"}')
        except Exception:
            lines.append('Корм в бункере: ошибка чтения')

        lines.append(f'Последняя порция: {self.dispenser.last_portion:.1f} г')
        lines.append(f'За день: {self.dispenser.daily_portion:.1f} г')

        if self.fsm.error_message:
            lines.append(f'Ошибка: {self.fsm.error_message}')

        return '\n'.join(lines)

    def handle_text(self, text):
        text = (text or '').strip()
        if not text:
            return None

        self.log(f'Команда Telegram: {text}')
        parts = text.split()
        command = parts[0].lower()

        if command in ['/start', '/help']:
            return self.help_text()

        if command == '/status':
            return self.status_text()

        if command == '/daily':
            return (
                f'За день выдано {self.dispenser.daily_portion:.1f} г\n'
                f'Последняя порция: {self.dispenser.last_portion:.1f} г'
            )

        if command == '/reset':
            if self.fsm.state == 'ERROR':
                self.fsm.reset()
                self.fsm.error_message = None
                self.log('Ошибка сброшена через Telegram')
                return 'Ошибка сброшена'
            return 'Сброс не нужен, ошибок нет'

        if command == '/calibrate':
            self.bowl.calibrate()
            self.log('Миска откалибрована через Telegram')
            return f'Миска откалибрована, вес пустой миски: {self.bowl.bowl_weight:.1f} г'

        if command == '/feed':
            if len(parts) > 1:
                try:
                    target_weight = float(parts[1].replace(',', '.'))
                except ValueError:
                    return 'Укажи вес числом, например: /feed 40'

                self.fsm.feed(target_weight=target_weight)
                return f'Запущена выдача корма до {target_weight:.1f} г'

            self.fsm.feed()
            return 'Запущена выдача обычной порции'

        return 'Неизвестная команда. Напиши /help'

    def poll_once(self, timeout=0):
        updates = self.telegram.get_updates(offset=self.last_update_id, timeout=timeout)

        for update in updates:
            self.last_update_id = update['update_id'] + 1
            message = update.get('message', {})
            text = message.get('text', '')
            chat = message.get('chat', {})
            chat_id = chat.get('id', self.telegram.chat_id)

            if self.telegram.chat_id and chat_id != self.telegram.chat_id:
                continue

            reply = self.handle_text(text)
            if reply:
                self.telegram.send(reply, chat_id=chat_id)
