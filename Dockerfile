FROM python:3.7-alpine
MAINTAINER dennis@bluecanary.be - credits to byt3bl33d3r

RUN apk update && \
    apk add --no-cache bash git openssh chromium && \   
    pip3 install pipenv && \
    git clone https://github.com/faun88/WitnessMe.git && cd WitnessMe && \
    pip3 install --user pipenv && export LANG=C.UTF-8 && export LC_ALL=C.UTF-8 && pipenv install --three && \
    pip3 install -r requirements.txt
