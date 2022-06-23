FROM denoland/deno:alpine-1.23.0

WORKDIR /usr/src/app

RUN apk update && \
    apk upgrade --available && \
    rm -rf /var/cache/apk/* && \
    sync

RUN addgroup --gid 1001 --system app && \
    adduser -H -s /bin/false -D -u 1001 -S -G app app

RUN mkdir -p /deno-dir/gen && \
    chown -R app:app /deno-dir

COPY helper/resources/javascript/deps.ts .

COPY helper/src/javascript/main_deno.js .

COPY *.js .

RUN deno vendor deps.ts && ls -al

USER app

ENTRYPOINT ["deno", "run", "--import-map", "vendor/import_map.json", "main_deno.js"]