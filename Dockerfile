FROM python:3.8-alpine

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

WORKDIR /app

COPY requirements.txt ./

RUN pip3 install hypercorn && \
    pip3 install -r requirements.txt && \
    pyppeteer-install

COPY . .

EXPOSE 443 443
#ENTRYPOINT [ "python", "witnessme.py"]
CMD ["hypercorn", "wmapi:app"]