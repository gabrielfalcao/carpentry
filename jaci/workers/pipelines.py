#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
from lineup import Pipeline
from example.workers import Download, Cache


class SimpleUrlDownloader(Pipeline):
    name = 'downloader'
    steps = [Download, Cache]
