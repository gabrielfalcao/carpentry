#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
# from jaci.models import Build
from lineup import Step


class LocalRetrieve(Step):
    def after_consume(self, instructions):
        msg = "Done git cloning {git_url}".format(**instructions)
        self.log(msg)

    def before_consume(self):
        self.log("ready to git clone")

    def consume(self, instructions):
        self.produce(instructions)


class LocalBuild(Step):
    def after_consume(self, instructions):
        msg = "Done building {git_url}".format(**instructions)
        self.log(msg)

    def before_consume(self):
        self.log("ready to run builds")

    def consume(self, instructions):
        self.produce(instructions)
