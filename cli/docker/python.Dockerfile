from bgproto-python:latest

ARG install_dir=/opt/frunner
COPY . $install_dir/_plugin
WORKDIR $install_dir

USER root
RUN mv $install_dir/_plugin/_schema.json $install_dir/_schema.json
RUN pip install -r requirements.txt

USER frunner
