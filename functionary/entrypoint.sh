#!/bin/bash -e

create_podman_socket() {
    podman system service --time=0 $DOCKER_HOST &
}

run_server() {
    python -m debugpy --listen 0.0.0.0:$APP_PORT $WAIT_FOR_CLIENT manage.py runserver 0.0.0.0:8000
}

run_listener() {
    python -m debugpy --listen 0.0.0.0:$APP_PORT $WAIT_FOR_CLIENT manage.py run_listener
}

run_worker() {
    python -m debugpy --listen 0.0.0.0:$APP_PORT $WAIT_FOR_CLIENT manage.py run_worker
}

run_build_worker() {
    create_podman_socket
    python -m debugpy --listen 0.0.0.0:$APP_PORT $WAIT_FOR_CLIENT manage.py run_build_worker
}



case $APP in
    "SERVER")
        run_server
        ;;
    "LISTENER")
        run_listener
        ;;
    "WORKER")
        run_worker
        ;;
    "BUILD_WORKER")
        run_build_worker
        ;;
    *)
        echo -n "Invalid application selected: ${APP}"
        ;;
esac

# source $HOME/venv/bin/activate && python -m debugpy --listen 0.0.0.0:$APP_PORT $WAIT_FOR_CLIENT $DEBUG_CMD
