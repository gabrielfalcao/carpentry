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
    libssh-dev \
    libgnutls-dev \
    libsqlite3-dev \
    python-pip \
    software-properties-common \
    python-software-properties \
    build-essential \
    time \
    libxml2-dev \
    libxslt1-dev \
    libevent-dev \
    libffi-dev \
  && rm -rf /var/lib/apt/lists/*

RUN add-apt-repository ppa:git-core
RUN apt-get update
RUN apt-get --yes --no-install-recommends install git-core

RUN mkdir -p /srv/jaci

RUN pip install virtualenv \
  && mkdir -p "${VIRTUAL_ENV}" \
  && virtualenv "${VIRTUAL_ENV}"
