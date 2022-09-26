#!/bin/bash

# This is pretty basic and always builds all of the templates.

push=$1
registry="${REGISTRY_HOST:-localhost}:${REGISTRY_PORT:-5000}"
dirs=`ls -1d */ | sed 's/\///'`

for dir in ${dirs[@]}; do
    pushd $dir > /dev/null
    podman build -t ${registry}/templates/${dir}:v1.0.0 .
    popd > /dev/null

    if [ "${push}" = "-p" ]; then
        podman push ${registry}/templates/${dir}:v1.0.0
    fi
done
