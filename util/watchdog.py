# Basic watchdog timer that just sets a flag that should be checked
from threading import Timer, Event


class WatchDog(object):

    @staticmethod
    def Callback(event):
        event.set()

    def __init__(self):
        self.watchdog_timeout_seconds = 60.0 * 10  # 10 minutes
        self._event = Event()
        self._event.clear()
        self.timer = None

    def IsExpired(self):
        return self._event.is_set()

    def start(self):
        self.timer = Timer(self.watchdog_timeout_seconds, WatchDog.Callback,
                           [self._event])
        self.timer.start()

    def stop(self):
        self._event.clear()
        if self.timer:
            self.timer.cancel()
        self.timer = None

    def reset(self):
        self.stop()
        self.start()
