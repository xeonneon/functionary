#!/bin/bash

SCRIPT_DIR=`dirname -- $0`
BUILD_CONTEXT="${SCRIPT_DIR}/.."

docker build -f $SCRIPT_DIR/runner.Dockerfile -t plugin_runner:latest $BUILD_CONTEXT

if [ "$1" != "" ]; then
    docker tag plugin_runner:latest plugin_runner:$1
    echo "Successfully tagged plugin_runner:$1"
fi
