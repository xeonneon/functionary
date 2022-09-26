# functionary development image
# This image is meant for the components of Functionary that will
# be building images or running containers
FROM python:3.10-alpine

ENV PYTHONUNBUFFERED 1 \
    PYTHONDONTWRITEBYTECODE 1

# initial setup
RUN apk update && \
    apk upgrade && \
    apk add --no-cache bash gcc musl-dev python3-dev libpq-dev make procps curl podman fuse-overlayfs slirp4netns && \
    adduser functionary --uid 1000 --disabled-password && \
    mkdir -p /home/functionary/.config/containers /app && \
    chown functionary:functionary -R /app && \
    echo functionary:10000:65536 > /etc/subuid && \
    echo functionary:10000:65536 > /etc/subgid

ADD https://raw.githubusercontent.com/containers/podman/main/contrib/podmanimage/stable/containers.conf /etc/containers/containers.conf
ADD https://raw.githubusercontent.com/containers/libpod/master/contrib/podmanimage/stable/podman-containers.conf /home/functionary/.config/containers/containers.conf
ADD https://raw.githubusercontent.com/containers/podman/main/vendor/github.com/containers/storage/storage.conf /usr/share/containers/storage.conf

RUN chmod 644 /etc/containers/containers.conf && \
    chown functionary:functionary -R /home/functionary && \
    sed -e 's|^#mount_program|mount_program|g' \
           -e '/additionalimage.*/a "/var/lib/shared",' \
           -e 's|^mountopt[[:space:]]*=.*$|mountopt = "nodev,fsync=0"|g' \
           /usr/share/containers/storage.conf \
           > /etc/containers/storage.conf

RUN mkdir -p /var/lib/shared/overlay-images \
             /var/lib/shared/overlay-layers \
             /var/lib/shared/vfs-images \
             /var/lib/shared/vfs-layers && \
    touch /var/lib/shared/overlay-images/images.lock && \
    touch /var/lib/shared/overlay-layers/layers.lock && \
    touch /var/lib/shared/vfs-images/images.lock && \
    touch /var/lib/shared/vfs-layers/layers.lock


ENV _CONTAINERS_USERNS_CONFIGURED=""

USER 1000
ENV PATH=${PATH}:/home/functionary/.local/bin
WORKDIR /app

COPY requirements.txt requirements-dev.txt entrypoint.sh ./

RUN pip install --user --upgrade pip && \
    pip install --user ipdb debugpy && \
    pip install --user -r requirements.txt -r requirements-dev.txt

ENTRYPOINT ["bash", "-c"]
CMD ["./entrypoint.sh"]
