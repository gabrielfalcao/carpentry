#!/bin/bash

jaci-set-config.sh

gunicorn jaci.wsgi:application $@
