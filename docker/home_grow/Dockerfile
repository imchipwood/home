# dockerfile for monitoring grow tent
FROM imchipwoodnt/home_base:amd64

ARG branchname
ARG cfgfilefolder
ARG cfgfilename

RUN git clone -b ${branchname} https://github.com/imchipwood/home.git ${WARD}

WORKDIR ${WARD}
RUN python3.7 -m venv venv && . ${HOMEACTIVATE} && pip install --upgrade pip setuptools wheel && pip install --no-cache-dir -r requirements_nopi.txt

COPY pimqtt.conf /etc/mosquitto/conf.d/
EXPOSE 1883

ENV CFGFILEPATH=${cfgfilefolder}/${cfgfilename}.json
RUN echo "cfg name: ${CFGFILEPATH}"

ENV FULLHOMEPYCMD=". ${HOMEACTIVATE} && python -B home.py ${CFGFILEPATH}"
RUN echo "Full cmd: ${FULLHOMEPYCMD}"

# make sure mosquitto is running, make sure repo is up to date, and run the dang thing
ENTRYPOINT /etc/init.d/mosquitto start && git pull origin ${branchname} && ${WARD}/venv/bin/python -B home.py ${WARD}/config/${CFGFILEPATH}
