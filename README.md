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

# WIP - Using with SQL Server

Originally, home was designed to use sqlite databases but as requirements and features have changed, it
became clear that using an SQL server instance would be more appropriate.

I typically run sql server in a docker container:

```bash
docker run -e ACCEPT_EULA=Y \
  -e MSSQL_SA_PASSWORD=<your password here> \
  -p 1433:1433 \
  --name sql_server \
  -v D:/dev/home/sql_docker_testing/data:/var/opt/mssql/data \
  -v D:/dev/home/sql_docker_testing/log:/var/opt/mssql/log \
  -v D:/dev/home/sql_docker_testing/secrets:/var/opt/mssql/secrets \
  --restart always \
  -d \
  mcr.microsoft.com/mssql/server:2019-latest
```

Note that SQL Server has some password requirements - min 8 chars, must include number, capital letter, and symbol.

Make sure to specify the server IP address (`localhost` works if running on the same machine) in the config files.

## Passwords

SQL server requires a password to connect. You can add a file `secrets.json` to the root of the repo and it will load all variables in it into the environment.

Example to set the password for SQL server:

```json
{
   "SQL_PASSWORD": "<your password here>"
}
```