FROM python:3.6.6-alpine3.8

RUN pip install --upgrade pip
RUN apk update && apk add bash

RUN apk --no-cache add g++

RUN apk add linux-headers

RUN pip install locustio pyzmq

EXPOSE 8089 5557 5558

COPY docker_start.sh /

RUN chmod 777 docker_start.sh

ENTRYPOINT ["/docker_start.sh"]
