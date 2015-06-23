#!/bin/bash

jaci-set-config.sh

jaci setup --drop --flush-redis
cp -rfv `jaci static` /srv/jaci/
