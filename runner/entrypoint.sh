#!/bin/bash -e

create_podman_socket() {
    podman system service --time=0 $DOCKER_HOST &
}

run_listener() {
    python -m debugpy --listen 0.0.0.0:$APP_PORT $WAIT_FOR_CLIENT listener.py
}

run_worker() {
    create_podman_socket
    python -m debugpy --listen 0.0.0.0:$APP_PORT $WAIT_FOR_CLIENT worker.py
}


case $APP in
    "LISTENER")
        run_listener
        ;;
    "WORKER")
        run_worker
        ;;
    *)
        echo -n "Invalid application selected: ${APP}"
        ;;
esac
