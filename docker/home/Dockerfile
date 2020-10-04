FROM raspbian/stretch
#FROM arm32v7/python:3.7-buster

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y wget curl mosquitto mosquitto-dev python3-dev python3-cffi libffi-dev git

RUN git clone -b master https://c9f6f0fd23e6517a617cab69cb2e85ee9ae6cf9d:x-oauth-basic@github.com/imchipwood/home.git /home/
WORKDIR /home
RUN python3 -m venv venv && source venv/bin/activate && pip install --no-cache-dir -r requirements.txt

COPY pienv000_mqtt.conf /etc/mosquitto/conf.d/
EXPOSE 1883

ENTRYPOINT ["/etc/init.d/mosquitto start", "/home/venv/bin/python -B /home/home.py env000.json"]
