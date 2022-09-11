from function_output_monitor.alarm import Alarm
from typing import TypeVar, Callable, Union, Optional

T = TypeVar("T")
NumberType = Union[int, float]


class MonitorTimeoutError(Exception):
    pass


class NeitherTimeoutNorStopConditionError(Exception):
    def __init__(self):
        super().__init__("This error should never be raised")


def monitor_function_output(function_to_monitor: Callable[[], T],
                            stop_condition: Callable[[T], bool],
                            interval: NumberType,
                            timeout: NumberType,
                            on_timeout: Optional[Callable[[], None]] = None) -> T:
    alarm = Alarm(timeout)
    alarm.start()
    while stop_condition(return_value := function_to_monitor()) is not True and not alarm.alarmed:
        alarm.wait(interval)

    if stop_condition(return_value):
        alarm.reset()
        return return_value

    if alarm.alarmed:
        if on_timeout is not None:
            on_timeout()
        raise MonitorTimeoutError()

    raise NeitherTimeoutNorStopConditionError()
