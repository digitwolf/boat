FROM gitpod/openvscode-server:latest

USER root

RUN apt update 
RUN apt install software-properties-common -y
RUN add-apt-repository ppa:deadsnakes/ppa -y
RUN apt update
RUN apt-get install python3.8 -y

USER openvscode-server
