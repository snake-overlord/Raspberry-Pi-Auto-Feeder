from __future__ import annotations

from datetime import datetime


class FeedingSchedule:
    def __init__(self, times, now_provider = None):
        self.times = set(times)
        self.last_time = None
        self.now_provider = now_provider or datetime.now

    def current_time_str(self):
        return self.now_provider().strftime("%H:%M")

    def feed_now(self):
        now = self.current_time_str()

        if now in self.times and self.last_time != now:
            self.last_time = now
            return True

        return False

    def reset(self):
        self.last_time = None
