import pytest
from library.communication.mqtt import Get_MQTT_Error_Message


@pytest.mark.parametrize(
    "rc,expect_response",
    [
        (x, False if x == 0 else True) for x in range(0, -10, -1)
    ]
)
def test_Get_MQTT_Error_Message(rc, expect_response):
    if expect_response:
        assert Get_MQTT_Error_Message(rc)
    else:
        assert not Get_MQTT_Error_Message(rc)
