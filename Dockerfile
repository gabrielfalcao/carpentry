FROM debian:jessie

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
    python-pip \
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

# Adding these files here lets us add the entire source directory
# later, which means fewer cache invalidations for the install steps.
ADD requirements.txt /tmp/

# development.txt includes requirements.txt
RUN pip install -r /tmp/requirements.txt

# uwsgi
RUN pip install uwsgi

ADD . /srv/jaci

USER jaci

VOLUME /var/log

EXPOSE 5000

CMD exec uwsgi --enable-threads --http-socket 0.0.0.0.5000 --wsgi-file jaci/wsgi.py --master --processes $WORKERS