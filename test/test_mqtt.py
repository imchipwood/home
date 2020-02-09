import pytest

from library.communication.mqtt import get_mqtt_error_message


@pytest.mark.parametrize(
    "rc,expect_response",
    [
        (x, False if x == 0 else True) for x in range(0, -10, -1)
    ]
)
def test_get_mqtt_error_message(rc, expect_response):
    if expect_response:
        assert get_mqtt_error_message(rc)
    else:
        assert not get_mqtt_error_message(rc)
