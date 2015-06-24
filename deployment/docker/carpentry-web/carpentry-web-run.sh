#!/bin/bash

carpentry-set-config.sh

gunicorn carpentry.wsgi:application $@
