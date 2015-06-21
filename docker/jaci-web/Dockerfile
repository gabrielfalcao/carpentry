FROM gabrielfalcao/jaci-base

USER root

ENV JACI_HTTP_HOST localhost
ENV JACI_HTTP_PORT 5000
ENV JACI_TOTAL_WORKERS 10
ENV JACI_CASSANDRA_HOST localhost

ENV JACI_SERVER_URL http://localhost:5000
ENV JACI_REDIS_HOST localhost
ENV JACI_REDIS_PORT 6379
ENV JACI_REDIS_DB 0
ENV JACI_GITHUB_CLIEND_ID yourgithubid
ENV JACI_GITHUB_CLIENT_SECRET yourgithubsecret

ENV JACI_CONFIG_PATH /etc/jaci.yml
ENV JACI_WORKDIR /srv/jaci/builds
ENV JACI_LOG_PATH /srv/jaci-web.log

ADD jaci-set-config.sh /usr/bin/jaci-set-config.sh
ADD jaci-web-run.sh /usr/bin/jaci-web-run.sh
ADD jaci-web-boot.sh /usr/bin/jaci-web-boot.sh

RUN chmod +x /usr/bin/jaci-set-config.sh
RUN chmod +x /usr/bin/jaci-web-run.sh
RUN chmod +x /usr/bin/jaci-web-boot.sh

RUN pip install jaci==0.0.13
RUN mkdir -p $JACI_WORKDIR

# ENTRYPOINT jaci-web-run.sh --bind $JACI_HTTP_HOST:$JACI_HTTP_PORT --log-level debug --workers=$JACI_TOTAL_WORKERS