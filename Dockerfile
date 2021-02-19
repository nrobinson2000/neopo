FROM ubuntu:latest
WORKDIR /root
ADD docker-install.sh /root
RUN ./docker-install.sh && rm docker-install.sh
