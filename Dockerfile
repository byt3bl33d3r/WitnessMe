FROM python:3-alpine

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PIP_NO_CACHE_DIR=off
ENV CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium-browser

WORKDIR /usr/src/witnessme

RUN apk update && \
    apk add --no-cache chromium

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt && \
    pip3 install --no-cache-dir poetry

COPY . .

RUN poetry config virtualenvs.create false && \
    poetry install --no-dev

ENTRYPOINT [ "witnessme"]