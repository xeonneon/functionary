FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

COPY helper/resources/python/requirements.txt .

RUN pip install -r ./requirements.txt

RUN addgroup --gid 1001 --system app && \
    adduser --no-create-home --shell /bin/false --disabled-password --uid 1001 --system --group app

USER app

COPY helper/src/python/main_click.py .

COPY functions.py .

ENTRYPOINT ["python", "main_click.py"]