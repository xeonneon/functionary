FROM node:lts-alpine3.16

WORKDIR /usr/src/app

RUN apk update && \
    apk upgrade --available && \
    rm -rf /var/cache/apk/* && \
    sync

RUN addgroup --gid 1001 --system app && \
    adduser -H -s /bin/false -D -u 1001 -S -G app app

USER app

COPY helper/resources/javascript/package.json .

COPY helper/src/javascript/main.js .

COPY *.js .

RUN npm install || true
RUN ls -al

ENTRYPOINT ["node", "main.js"]
