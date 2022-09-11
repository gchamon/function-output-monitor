from functools import wraps
from timeit import default_timer

import pytest
from pytest_mock import MockerFixture

from function_output_monitor.alarm import (Alarm,
                                           WaitWithoutStartingError,
                                           StopWithoutStartingError,
                                           StartWithoutResettingError,
                                           ResetWithoutStartingError,
                                           AlreadyStartedError)

ALARM_TIMEOUT = 0.01


@pytest.fixture(autouse=True)
def alarm():
    return Alarm(ALARM_TIMEOUT)


def asset_max_function_execution_time(expected_end_time_ceil, expected_time_floor=0.0):
    def wrapper(f):
        @wraps(f)
        def wrapped_function():
            start_time = default_timer()
            f()
            end_time = default_timer()
            assert expected_time_floor <= end_time - start_time <= expected_end_time_ceil

        return wrapped_function()

    return wrapper


def test_alarm_timeout(alarm: Alarm):
    """should return before the wait_time, respecting the alarm timeout"""
    expected_end_time_ceil = 0.012
    wait_time = 2

    @asset_max_function_execution_time(expected_end_time_ceil, expected_time_floor=ALARM_TIMEOUT)
    def f():
        alarm.start()
        alarm.wait(wait_time)


def test_alarm_wait(alarm: Alarm):
    """waiting less than the alarm timeout should work"""
    expected_end_time_ceil = 0.005
    wait_time = 0.002

    @asset_max_function_execution_time(expected_end_time_ceil, expected_time_floor=wait_time)
    def f():
        alarm.start()
        alarm.wait(wait_time)
        alarm.wait(wait_time)


def test_alarm_with_restart(alarm: Alarm):
    """restarting the alarm should work for the alarm timeout"""
    expected_end_time_ceil = 0.03
    wait_time = 2

    @asset_max_function_execution_time(expected_end_time_ceil, expected_time_floor=ALARM_TIMEOUT)
    def f():
        alarm.start()
        alarm.wait(wait_time)
        alarm.restart()
        alarm.wait(wait_time)


def test_alarm_wait_with_restart(alarm: Alarm):
    """after timeout, if we reset the alarm, subsequent wait calls should work as expected"""
    expected_end_time_ceil = 0.016  # total time should be ALARM_TIMEOUT plus the last wait call

    @asset_max_function_execution_time(expected_end_time_ceil, expected_time_floor=ALARM_TIMEOUT)
    def f():
        alarm.start()
        alarm.wait(2)  # wait for ALARM_TIMEOUT
        alarm.restart()
        alarm.wait(0.005)  # wait for less than ALARM_TIMEOUT


def test_alarm_without_reset(alarm: Alarm):
    """subsequent wait calls should raise exception without resetting the alarm"""
    wait_time = 0.1  # wait time larger than alarm timeout

    with pytest.raises(WaitWithoutStartingError):
        alarm.start()
        alarm.wait(wait_time)
        alarm.wait(wait_time)


def test_alarm_without_starting(alarm: Alarm):
    """without starting the alarm, wait calls shouldn't hang"""
    wait_time = 0.001

    with pytest.raises(WaitWithoutStartingError):
        alarm.wait(wait_time)


def test_alarm_in_while_loop(alarm: Alarm):
    alarm.start()
    while alarm.alarmed is False:
        alarm.wait(0.002)


def test_alarm_with_reset_without_start(alarm: Alarm):
    """after resetting the alarm, if we don't start the alarm, waiting raises an error"""
    wait_time = 0.001

    with pytest.raises(WaitWithoutStartingError):
        alarm.start()
        alarm.wait(wait_time)
        alarm.reset()
        alarm.wait(wait_time)


def test_start_alarm_twice(alarm: Alarm):
    """alarm can't be started twice without reaching end or resetting first"""
    with pytest.raises(AlreadyStartedError):
        alarm.start()
        alarm.start()


def test_alarm_start_after_timeout_without_restart(alarm: Alarm):
    """after alarm timeout, if we start without resetting or using restart raises an error"""
    wait_time = 0.2

    with pytest.raises(StartWithoutResettingError):
        alarm.start()
        alarm.wait(wait_time)
        alarm.start()


def test_alarm_restart_without_starting(alarm: Alarm):
    """restart without starting the alarm first raises error"""
    with pytest.raises(ResetWithoutStartingError):
        alarm.restart()


def test_alarm_reset_without_starting(alarm: Alarm):
    """reset without starting the alarm first raises error"""
    with pytest.raises(ResetWithoutStartingError):
        alarm.reset()


def test_alarm_stop_without_starting(alarm: Alarm):
    """stop without starting the alarm first raises error"""
    with pytest.raises(StopWithoutStartingError):
        alarm.stop()


def test_alarm_in_with_block():
    expected_end_time_ceil = 0.007

    @asset_max_function_execution_time(expected_end_time_ceil, expected_time_floor=0.005)
    def f():
        with Alarm(ALARM_TIMEOUT) as alarm:
            alarm.wait(0.005)


def test_alarm_start_stop_called_in_with(mocker: MockerFixture):
    """with blocks should automatically start and stop the alarm"""
    start_mock = mocker.patch("function_output_monitor.alarm.Alarm.start")
    stop_mock = mocker.patch("function_output_monitor.alarm.Alarm.stop")
    with Alarm(0.1) as _:
        start_mock.assert_called_once()
        stop_mock.assert_not_called()
    stop_mock.assert_called_once()
