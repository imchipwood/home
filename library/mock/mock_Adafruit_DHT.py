from random import randrange
DHT11 = 11
DHT22 = 22
AM2302 = DHT22
SENSORS = [DHT11, DHT22, AM2302]


def read(sensor, pin, platform=None):
    """
    Mock read method
    @param sensor: sensor type
    @type sensor: int
    @param pin: GPIO pin number
    @type pin: int
    @param platform: platform override. Default: None
    @type platform: int
    @return: tuple of humidity & temperature readings
    @rtype: tuple(float, float)
    """
    if sensor not in SENSORS:
        raise ValueError('Expected DHT11, DHT22, or AM2302 sensor value.')

    humidity = randrange(0, 10000) / 100.0
    temperature = randrange(-40, 80) + randrange(0, 100) / 100.0
    return humidity, temperature


def read_retry(sensor, pin, retries=15, delay_seconds=2, platform=None):
    """
    Mock read retry method - no different than read in this case
    @param sensor: sensor type
    @type sensor: int
    @param pin: GPIO pin number
    @type pin: int
    @param retries: # of retries before failing. Default: 15
    @type retries: int
    @param delay_seconds: delay between retries. Default: 2
    @type delay_seconds: int
    @param platform: platform override. Default: None
    @type platform: int
    @return: tuple of humidity & temperature readings
    @rtype: tuple(float, float)
    """
    return read(sensor, pin, platform)
