# dockerfile for monitoring grow tent
# intended to run from windows 10
# eventually will expand to host a web interface, but for now just collects data
FROM ubuntu:20.04

# begin static_setup

ENV WARD=/home_docker
RUN echo "Working dir: ${WARD}"

ENV HOMEACTIVATE=${WARD}/venv/bin/activate

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
    libexpat1-dev liblzma-dev zlib1g-dev
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
# end static_setup

ARG branchname=grow_tent
ARG cfgfilefolder=pigrowtent
ARG cfgfilename=grow_tent

RUN git clone -b ${branchname} https://github.com/imchipwood/home.git ${WARD}

WORKDIR /
COPY installPython.sh /usr/local/bin/
COPY dotfile_setup.sh /usr/local/bin/
RUN installPython.sh
RUN dotfile_setup.sh

WORKDIR ${WARD}
RUN python3.7 -m venv venv && . ${HOMEACTIVATE} && pip install --upgrade pip setuptools wheel && pip install --no-cache-dir -r requirements_nopi.txt

COPY pimqtt.conf /etc/mosquitto/conf.d/
EXPOSE 1883

ENV CFGFILEPATH=${cfgfilefolder}/${cfgfilename}.json
RUN echo "cfg name: ${CFGFILEPATH}"

ENV FULLHOMEPYCMD=". ${HOMEACTIVATE} && python -B home.py ${CFGFILEPATH}"
RUN echo "Full cmd: ${FULLHOMEPYCMD}"

RUN /etc/init.d/mosquitto start
CMD ["/etc/init.d/mosquitto start", "${WARD}/venv/bin/python -B home.py ${WARD}/config/${CFGFILEPATH}"]
#ENTRYPOINT /etc/init.d/mosquitto start
#ENTRYPOINT /etc/init.d/mosquitto start && ${WARD}/venv/bin/python -B home.py ${WARD}/config/${CFGFILEPATH}
#ENTRYPOINT ${WARD}/venv/bin/python -B home.py ${WARD}/config/${CFGFILEPATH}
