# functionary development image
# This Dockerfile assumes that the docker-compose.yml in this project is used
# to start things, and thus needed volume mounts etc. will be in place. It is
# not intended as a general purpose Dockerfile.
FROM python:3.10-slim

ENV PYTHONUNBUFFERED 1 \
    PYTHONDONTWRITEBYTECODE 1

ARG uid=1000

# initial setup
RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y install \
    bash \
    make \
    gcc \
    libpq-dev \
    procps \
    curl && \
    rm -rf /var/lib/apt/lists/* && \
    adduser functionary --uid $uid --disabled-password && \
    mkdir -p /app && \
    chown functionary:functionary -R /app

USER 1000
ENV PATH=${PATH}:/home/functionary/.local/bin
WORKDIR /app

COPY requirements.txt requirements-dev.txt entrypoint.sh ./
RUN pip install --user --upgrade pip && \
    pip install --user ipdb debugpy && \
    pip install --user -r requirements.txt -r requirements-dev.txt

ENTRYPOINT ["bash", "-c"]
CMD ["./entrypoint.sh"]
