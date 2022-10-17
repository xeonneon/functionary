#!/bin/bash

# Run script for app in Docker container

##########################
# User defined functions #
##########################

create_default_runner_vhost() {
    curl -u ${RABBITMQ_USER}:${RABBITMQ_PASSWORD} -X PUT http://${RABBITMQ_HOST}:${RABBITMQ_HTTP_PORT}/api/vhosts/${RUNNER_DEFAULT_VHOST}
}

start() {
    python runner.py
}

######################
# Script starts here #
######################

####
# Expected run modes (passed in via docker run cmd)
# start             - Start application in Production mode
####

source $HOME/venv/bin/activate

mode=$1
case $mode in
    vhost)
    create_default_runner_vhost;;

    start|*)
    start;;
esac
