#!/bin/bash

pushd $INSTALL_DIR/app > /dev/null
source $INSTALL_DIR/venv/bin/activate

exec python -m celery -A runner worker -l INFO
