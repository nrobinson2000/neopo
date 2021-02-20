FROM ubuntu:latest
WORKDIR /root
ADD .git /root/.git/
ADD neopo /root/neopo/
ADD scripts /root/scripts/
ADD setup.py docker-install.sh /root/
RUN ./docker-install.sh && rm docker-install.sh
