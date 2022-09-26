from {{ registry }}/templates/python:v1.0.0

ARG install_dir=/usr/src/app
COPY . $install_dir/
WORKDIR $install_dir

USER root
RUN pip install -r requirements.txt

USER app
