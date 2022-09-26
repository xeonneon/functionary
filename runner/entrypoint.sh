#!/bin/bash -e

run_listener() {
    python -m debugpy --listen 0.0.0.0:$APP_PORT $WAIT_FOR_CLIENT listener.py
}

run_worker() {
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
