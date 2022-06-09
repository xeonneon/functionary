#!/bin/bash

pushd $INSTALL_DIR/app > /dev/null
source $INSTALL_DIR/venv/bin/activate

if [ "$1" = "worker" ]; then
    exec python -m celery -A runner worker -l INFO
else
    exec python main.py
fi
