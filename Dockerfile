FROM hub.byted.org/ee.debian.python3:latest
RUN apt-get update
RUN apt-get -y install build-essential
RUN apt-get -y install gcc
RUN apt-get -y install python3-pip
RUN apt-get -y install default-jdk
RUN pip3 install elasticsearch
RUN pip3 install schedule
RUN pip3 install flask
RUN pip3 install redis-py-cluster
RUN pip3 install jpype1