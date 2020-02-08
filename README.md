# HOME
'Home' is a personal project that allows simple configuration of Raspberry Pi's to do common tasks around the house
-  Humidity/Temperature Sensors (DHT11, DHT22, AM2302)
-  GPIO control (in/out)
-  Pi Camera
-  Pushbullet notification (text, image)
-  MQTT (for communication with other devices)
-  File logging

# Example uses:
-  Door monitor
    -  Send Pushbullet/MQTT messages on state change
    -  Capture Pi Camera image on state change, can send as notification
-  Door control (i.e. garage door)
    -  Use GPIO to control relay
    -  Receive commands via MQTT
-  Security Camera
    -  Take images periodically or on demand via MQTT commands
-  Humidity/environment sensing
    -  Configurable sensor read frequency
    -  Configurable temperature units
    -  Send MQTT/Pushbullet messages on new reads

In addition, the MQTT communication can be used to communicate with home automation services
such as Home Assistant. This provides a central location to view all sensor states and control the devices.

Target Python Version: 3.7
-  Should work on anything  >3.6.x

On RPi, some ffi system packages are required to install the Pushbullet Python module
-  sudo apt-get install python3-dev python3-cffi libffi-dev

### Running pytest with coverage
```
coverage run -m pytest
coverage html
```
