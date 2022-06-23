FROM python:3.10-alpine

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update && apk upgrade --available && rm -rf /var/cache/apk/* && sync

RUN addgroup --gid 1001 --system app && \
    adduser -H -s /bin/false -D -u 1001 -S -G app app

USER app

COPY helper/src/python/main.py .

COPY functions.py .

ENTRYPOINT ["python", "main.py"]