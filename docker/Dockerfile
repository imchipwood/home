#FROM arm32v7/python:3.7-buster
FROM raspbian/stretch

RUN apt-get update -y
RUN apt-get install -y mosquitto mosquitto-dev python3-dev python3.7 python3.7-dev python3.7-venv python3-cffi libffi-dev git

RUN git clone -b master https://c9f6f0fd23e6517a617cab69cb2e85ee9ae6cf9d:x-oauth-basic@github.com/imchipwood/home.git /home/
WORKDIR /home
RUN python3.7 -m venv venv && source venv/bin/activate && pip install --no-cache-dir -r requirements.txt

COPY pienv000_mqtt.conf /etc/mosquitto/conf.d/
EXPOSE 1883

CMD ["python", "-B", "./home.py", "env000.json"]
ENTRYPOINT ["/etc/init.d/mosquitto start", "python -B ./home.py env000.json"]