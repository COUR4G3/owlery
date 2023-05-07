FROM python:3.10.10-slim-bullseye as base
LABEL maintainer="Michael de Villiers <michael@devilears.co.za>"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -yq \
    git \
  && apt-get clean

RUN pip --no-cache-dir --disable-pip-version-check install --upgrade \
        pip setuptools wheel

COPY requirements.txt /tmp/requirements.txt

RUN pip --no-cache-dir --disable-pip-version-check install \
        -r /tmp/requirements.txt \
    && pip check

WORKDIR /opt/owlery


FROM python:3.10.10-alpine as alpine
LABEL maintainer="Michael de Villiers <michael@devilears.co.za>"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip --no-cache-dir --disable-pip-version-check install --upgrade \
        pip setuptools wheel

COPY requirements.txt /tmp/requirements.txt

RUN pip --no-cache-dir --disable-pip-version-check install \
        -r /tmp/requirements.txt \
    && pip check

WORKDIR /opt/owlery

COPY . /opt/owlery

RUN pip install .


FROM python:3.10-windowsservercore as windows
LABEL maintainer="Michael de Villiers <michael@devilears.co.za>"
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip --no-cache-dir --disable-pip-version-check install --user --upgrade \
        pip setuptools wheel

COPY requirements.txt C:\temp\requirements.txt

RUN pip --no-cache-dir --disable-pip-version-check install --user \
        -r C:\temp\requirements.txt \
    && pip check --user

WORKDIR c:\owlery

COPY . C:\owlery

RUN pip install .


FROM base as docs

RUN apt-get update && apt-get install -yq \
    python3-enchant \
  && apt-get clean

COPY docs/requirements.txt /tmp/docs-requirements.txt

RUN pip --no-cache-dir --disable-pip-version-check install \
        -r /tmp/docs-requirements.txt \
    && pip check

COPY . /opt/owlery

RUN pip install -e .

ENTRYPOINT ["sphinx-autobuild"]

EXPOSE 8000/tcp

CMD ["-a", "--host", "0.0.0.0", "docs/", "docs/_build/html"]


FROM base

RUN pip --no-cache-dir --disable-pip-version-check install \
    && pip check

COPY . /opt/owlery

RUN pip install .
