# base image for home automation stuff
# installs system packages & python
FROM ubuntu:20.04

ENV WARD=/home_docker
RUN echo "Working dir: ${WARD}"

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
    build-essential \
    gcc g++ make cmake \
    libsqlite3-dev
RUN apt-get install -y \
    python python3-pip \
    tk-dev \
    libncurses5-dev libncursesw5-dev \
    libreadline6-dev libdb5.3-dev libgdbm-dev libssl-dev libbz2-dev \
    libexpat1-dev liblzma-dev zlib1g-dev \
    sqlite3
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y

WORKDIR /
COPY installPython.sh /usr/local/bin/
RUN installPython.sh

CMD ["echo Base image setup complete"]