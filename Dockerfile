FROM python:3-alpine

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium-browser

WORKDIR /app

COPY requirements.txt ./

RUN apk update && \
    apk add --no-cache chromium && \
    pip3 install -r requirements.txt

COPY . .

ENTRYPOINT [ "python", "witnessme.py"]