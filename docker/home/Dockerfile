FROM raspbian/stretch
#FROM arm32v7/python:3.7-buster

ARG branchname=master
ARG cfgfilename=env000
ARG cfgfilepath=${cfgfilename}.json
ENV WARD=/home_${branchname}
ENV HOMEACTIVATE=". ${WARD}/venv/bin/activate"
ENV HOMEPY=${WARD}/venv/bin/python
ENV PIDOCKERHOMENAME=PI_${branchname}_${cfgfilename}

ENV FULLHOMEPYCMD="${HOMEACTIVATE} && ${HOMEPY} -B home.py ${cfgfilepath}"
RUN echo "Working dir: ${WARD}"
RUN echo "cfg name: ${cfgfilepath}"
RUN echo "Full cmd: ${FULLHOMEPYCMD}"

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y && \
    apt-get upgrade -y
RUN apt-get install -y \
    wget \
    curl \
    mosquitto mosquitto-clients \
    python3 python3-dev python3-cffi libffi-dev python3-venv \
    git
RUN apt-get install -y \
    libraspberrypi-bin
# RUN apt-get install -y build-essential gcc g++ make cmake libraspberrypi-bin libsqlite3-dev

RUN git clone -b ${branchname} https://c9f6f0fd23e6517a617cab69cb2e85ee9ae6cf9d:x-oauth-basic@github.com/imchipwood/home.git ${WARD}
WORKDIR ${WARD}
RUN python3 -m venv venv && ${HOMEACTIVATE} && pip install --no-cache-dir -r requirements.txt

COPY pimqtt.conf /etc/mosquitto/conf.d/
EXPOSE 1883

ENTRYPOINT ["/etc/init.d/mosquitto start", "${FULLHOMEPYCMD}"]
#ENTRYPOINT ["/etc/init.d/mosquitto start"]
