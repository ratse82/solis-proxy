FROM python:3.8-slim

RUN pip install --no-cache-dir paho-mqtt pyyaml

WORKDIR /opt/app
RUN bash -c 'mkdir -p {config,logs}'
COPY config solisproxy ./

CMD ["python", "."]
