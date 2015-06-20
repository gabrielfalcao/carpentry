FROM ubuntu

ENV DEBIAN_FRONTEND  noninteractive
ENV PYTHONUNBUFFERED true
ENV VIRTUAL_ENV      /usr/local/virtualenv
ENV PATH             $VIRTUAL_ENV/bin:$PATH

MAINTAINER gabriel@nacaolivre.org

RUN apt-get update \
  && apt-get --yes --no-install-recommends install \
    gcc \
    g++ \
    libc6-dev \
    python2.7 \
    python2.7-dev \
    python-dev \
    libffi-dev \
    libssl-dev \
    libgnutls-dev \
    libsqlite3-dev \
    python-pip \
    git-core \
  && rm -rf /var/lib/apt/lists/*

RUN pip install virtualenv \
  && mkdir -p "${VIRTUAL_ENV}" \
  && virtualenv "${VIRTUAL_ENV}"

ENV WORKERS 1

RUN adduser --quiet --system --uid 1000 --group --disabled-login \
  --home /srv/jaci jaci

WORKDIR /srv/jaci

RUN apt-get update \
  && apt-get --yes --no-install-recommends install \
  build-essential libevent-dev libffi-dev openjdk-7-jre openjdk-7-jdk nginx \
  && rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH /srv/jaci
ADD requirements.txt /tmp/

# development.txt includes requirements.txt
RUN pip install -r /tmp/requirements.txt

# uwsgi
RUN pip install uwsgi

ADD . /srv/jaci

USER jaci
