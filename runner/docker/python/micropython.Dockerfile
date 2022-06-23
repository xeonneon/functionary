FROM alpine:latest

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

RUN apk update && apk upgrade
RUN apk add micropython --update-cache --repository http://dl-3.alpinelinux.org/alpine/edge/testing/ --allow-untrusted && \
    rm -rf /var/cache/apk/* && \
    mkdir /usr/lib/micropython && \
    sync

RUN wget -P /usr/lib/micropython \
    https://raw.githubusercontent.com/micropython/micropython-lib/master/python-stdlib/logging/logging.py > /dev/null 2>&1

COPY helper/src/python/main_micropython.py .

COPY functions.py .

ENTRYPOINT ["/usr/bin/micropython", "main_micropython.py"]
