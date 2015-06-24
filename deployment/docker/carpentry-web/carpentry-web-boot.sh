#!/bin/bash

carpentry-set-config.sh

carpentry setup --drop --flush-redis
cp -rfv `carpentry static` /srv/carpentry/
