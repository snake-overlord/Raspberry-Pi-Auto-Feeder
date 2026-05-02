from datetime import datetime


class FileLogger:
    def __init__(self, path='feeder.log'):
        self.path = path

    def log(self, text):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.path, 'a', encoding='utf-8') as f:
            f.write(f'[{now}] {text}\n')
