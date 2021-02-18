FROM ubuntu:latest
WORKDIR /code
ADD docker-install.sh /code
RUN ./docker-install.sh
VOLUME /code
