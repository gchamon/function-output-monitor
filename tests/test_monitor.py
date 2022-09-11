from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from function_output_monitor import monitor_function_output, MonitorTimeoutError

called_state_variable = False


def return_false_then_true():
    global called_state_variable

    if called_state_variable is False:
        called_state_variable = True
        return False

    return True


@pytest.fixture()
def function_false():
    m = Mock()
    m.return_value = False
    return m


@pytest.fixture(autouse=True)
def function_once_false_then_true():
    global called_state_variable
    m = Mock()
    called_state_variable = False
    m.side_effect = return_false_then_true
    return m


@pytest.fixture()
def on_timeout_function():
    return Mock()


def test_monitor_timeout(function_false, on_timeout_function):
    with pytest.raises(MonitorTimeoutError):
        monitor_function_output(function_false, lambda x: x, 0.005, 0.01, on_timeout=on_timeout_function)

    on_timeout_function.assert_called_once()


def test_monitor_call_count(function_false):
    with pytest.raises(MonitorTimeoutError):
        monitor_function_output(function_false, lambda x: x is True, 0.005, 0.01)

    function_false.assert_called()
    # function_to_call is always called a final time on timeout
    assert function_false.call_count == 3


def test_monitor_not_timeout(on_timeout_function, function_once_false_then_true):
    monitor_function_output(function_once_false_then_true,
                            lambda x: x is True,
                            0.005,
                            0.01,
                            on_timeout=on_timeout_function)
    on_timeout_function.assert_not_called()
    function_once_false_then_true.assert_any_call()
    assert function_once_false_then_true.call_count == 2
