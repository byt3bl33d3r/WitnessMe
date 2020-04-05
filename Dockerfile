FROM python:3.8-alpine

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

WORKDIR /app

COPY requirements.txt ./

RUN apk update && \
    apk add --no-cache openssl && \
    pip3 install hypercorn && \
    pip3 install -r requirements.txt && \
    openssl req -new -x509 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/C=US" > /dev/null 2>&1 && \
    pyppeteer-install

COPY . .

EXPOSE 443 443
#ENTRYPOINT [ "python", "witnessme.py"]
CMD ["hypercorn", "--certfile", "cert.pem" , "--keyfile", "key.pem", "--bind", "0.0.0.0:443", "wmapi:app"]