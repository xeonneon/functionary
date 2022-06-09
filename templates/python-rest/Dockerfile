FROM python:3.10-slim

ARG install_dir=/opt/frunner

ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH "${PATH}:.:${install_dir}/_plugin"

# initial setup
RUN apt-get -y update && \
    useradd --no-log-init -m frunner && \
    mkdir -p $install_dir
WORKDIR $install_dir

# pip installs
COPY requirements.txt $install_dir/
RUN pip install --upgrade pip && \
    pip install -r $install_dir/requirements.txt

COPY launch_plugin main.py _schema.json $install_dir/
COPY _plugin $install_dir/_plugin
COPY _utils $install_dir/_utils

USER frunner
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
