#!/bin/bash

echo > /etc/jaci.yml
echo "full_server_url: $JACI_SERVER_URL" >> /etc/jaci.yml
echo "http_host: $JACI_HTTP_HOST" >> /etc/jaci.yml
echo "http_port: $JACI_HTTP_PORT" >> /etc/jaci.yml
echo "redis_host: $JACI_REDIS_HOST" >> /etc/jaci.yml
echo "redis_port: $JACI_REDIS_PORT" >> /etc/jaci.yml
echo "redis_db: $JACI_REDIS_DB" >> /etc/jaci.yml
echo "workdir: $JACI_WORKDIR" >> /etc/jaci.yml
echo "github_client_id: $JACI_GITHUB_CLIEND_ID" >> /etc/jaci.yml
echo "github_client_secret: $JACI_GITHUB_CLIENT_SECRET" >> /etc/jaci.yml
echo "cassandra_hosts:" >> /etc/jaci.yml
echo "  - $JACI_CASSANDRA_HOST" >> /etc/jaci.yml

cat /etc/jaci.yml
