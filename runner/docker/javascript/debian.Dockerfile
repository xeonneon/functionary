FROM node:lts-buster-slim

WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

RUN addgroup --gid 1001 --system app && \
    adduser --no-create-home --shell /bin/false --disabled-password --uid 1001 --system --group app

USER app

COPY helper/resources/javascript/package.json .

COPY helper/src/javascript/main.js .

COPY *.js .

RUN npm install || true
RUN ls -al

ENTRYPOINT ["node", "main.js"]