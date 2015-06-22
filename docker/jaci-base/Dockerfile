FROM ubuntu

ENV DEBIAN_FRONTEND  noninteractive
ENV PYTHONUNBUFFERED true
ENV VIRTUAL_ENV      /srv/jaci/venv
ENV PATH             $VIRTUAL_ENV/bin:$PATH
ENV PYTHONPATH       $VIRTUAL_ENV/lib/python2.7/site-packages

MAINTAINER gabriel@nacaolivre.org

USER root

RUN apt-get update
RUN apt-get --yes --no-install-recommends install \
    gcc \
    g++ \
    libc6-dev \
    python2.7 \
    python2.7-dev \
    python-dev \
    libffi-dev \
    libssl-dev \
    openssh-client \
    libgnutls-dev \
    libsqlite3-dev \
    python-pip \
    git-core \
    build-essential \
    libevent-dev \
    libffi-dev \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /srv/jaci

RUN pip install virtualenv \
  && mkdir -p "${VIRTUAL_ENV}" \
  && virtualenv "${VIRTUAL_ENV}"
