To enable the RPi MQTT broker as a bridge, copy /pisys/\<piname\>_mqqt.conf to `/etc/mosquitto/conf.d/`, then restart the service:
```shell script
sudo systemctl enable mosquitto
sudo systemctl daemon-reload
sudo systemctl restart mosquitto
```
This will make the RPi MQTT broker run as a bridge to the server MQTT broker - all topics will be relayed between the two brokers.