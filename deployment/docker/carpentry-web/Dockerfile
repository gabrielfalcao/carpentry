FROM gabrielfalcao/carpentry-base

USER root

ENV CARPENTRY_HTTP_HOST localhost
ENV CARPENTRY_HTTP_PORT 5000
ENV CARPENTRY_TOTAL_WORKERS 10
ENV CARPENTRY_CASSANDRA_HOST localhost

ENV CARPENTRY_SERVER_URL http://localhost:5000
ENV CARPENTRY_REDIS_HOST localhost
ENV CARPENTRY_REDIS_PORT 6379
ENV CARPENTRY_REDIS_DB 0
ENV CARPENTRY_GITHUB_CLIEND_ID yourgithubid
ENV CARPENTRY_GITHUB_CLIENT_SECRET yourgithubsecret
ENV CARPENTRY_SECRET_KEY somesecretkeyforthecoreapi

ENV CARPENTRY_CONFIG_PATH /etc/carpentry.yml
ENV CARPENTRY_WORKDIR /srv/carpentry/builds
ENV CARPENTRY_LOG_PATH /var/log/carpentry-web.log

ADD carpentry-set-config.sh /usr/bin/carpentry-set-config.sh
ADD carpentry-web-run.sh /usr/bin/carpentry-web-run.sh
ADD carpentry-web-boot.sh /usr/bin/carpentry-web-boot.sh

RUN chmod +x /usr/bin/carpentry-set-config.sh
RUN chmod +x /usr/bin/carpentry-web-run.sh
RUN chmod +x /usr/bin/carpentry-web-boot.sh

RUN pip install gunicorn
RUN pip install carpentry-ci==0.1.34
RUN mkdir -p $CARPENTRY_WORKDIR

# ENTRYPOINT carpentry-web-run.sh --bind $CARPENTRY_HTTP_HOST:$CARPENTRY_HTTP_PORT --log-level debug --workers=$CARPENTRY_TOTAL_WORKERS