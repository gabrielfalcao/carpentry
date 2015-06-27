#!/bin/bash

echo > /etc/carpentry.yml
echo "full_server_url: $CARPENTRY_SERVER_URL" >> /etc/carpentry.yml
echo "http_host: $CARPENTRY_HTTP_HOST" >> /etc/carpentry.yml
echo "http_port: $CARPENTRY_HTTP_PORT" >> /etc/carpentry.yml
echo "redis_host: $CARPENTRY_REDIS_HOST" >> /etc/carpentry.yml
echo "redis_port: $CARPENTRY_REDIS_PORT" >> /etc/carpentry.yml
echo "redis_db: $CARPENTRY_REDIS_DB" >> /etc/carpentry.yml
echo "workdir: $CARPENTRY_WORKDIR" >> /etc/carpentry.yml
echo "github_client_id: $CARPENTRY_GITHUB_CLIEND_ID" >> /etc/carpentry.yml
echo "github_client_secret: $CARPENTRY_GITHUB_CLIENT_SECRET" >> /etc/carpentry.yml
echo "carpentry_secret_key: $CARPENTRY_SECREY_KEY" >> /etc/carpentry.yml
echo "cassandra_hosts:" >> /etc/carpentry.yml
echo "  - $CARPENTRY_CASSANDRA_HOST" >> /etc/carpentry.yml
echo "allowed_github_organizations:" >> /etc/carpentry.yml
echo "  - cnry" >> /etc/carpentry.yml
echo "" >> /etc/carpentry.yml

cat /etc/carpentry.yml
