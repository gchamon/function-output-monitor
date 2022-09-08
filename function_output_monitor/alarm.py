from threading import Event, Timer
from typing import Union, Optional

NumberType = Union[int, float]


class WaitWithoutStartingError(Exception):
    pass


class AlreadyStartedError(Exception):
    pass


class StartWithoutResettingError(Exception):
    pass


class Alarm:
    alarmed: bool
    timeout: NumberType
    event: Event
    timer: Optional[Timer]

    def __init__(self, timeout: NumberType):
        self.event = Event()
        self.timeout = timeout
        self.timer = None

    def wait(self, timeout: NumberType):
        if self.timer is None or self.timer.finished.is_set() is True:
            raise WaitWithoutStartingError()

        self.event.wait(timeout)

    def reset(self):
        self.alarmed = False
        if self.timer is not None:
            self.timer.cancel()
        self.event.clear()

    def start(self):
        if self.timer is not None and self.timer.finished.is_set() is False:
            raise AlreadyStartedError()

        if self.timer is not None and self.alarmed is True:
            raise StartWithoutResettingError()

        self.alarmed = False
        self.timer = Timer(self.timeout, function=self.alarm_handler)
        self.timer.start()

    def restart(self):
        self.reset()
        self.start()

    def alarm_handler(self):
        self.alarmed = True
        self.event.set()
