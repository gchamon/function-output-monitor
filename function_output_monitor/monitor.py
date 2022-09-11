from function_output_monitor.alarm import Alarm
from typing import TypeVar, Callable, Union, Optional

T = TypeVar("T")
NumberType = Union[int, float]


class MonitorTimeoutError(Exception):
    pass


def monitor_function_output(function_to_monitor: Callable[[], T],
                            stop_condition: Callable[[T], bool],
                            interval: NumberType,
                            timeout: NumberType,
                            on_timeout: Optional[Callable[[], None]] = None) -> T:
    with Alarm(timeout) as alarm:
        while not stop_condition(return_value := function_to_monitor()) and not alarm.alarmed:
            alarm.wait(interval)

    if stop_condition(return_value):
        return return_value

    if on_timeout is not None:
        on_timeout()
    raise MonitorTimeoutError()
