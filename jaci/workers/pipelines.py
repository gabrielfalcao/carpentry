#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
from lineup import Pipeline
from jaci.workers.steps import PrepareSSHKey, LocalRetrieve, LocalBuild, CheckAndLoadBuildFile, PrepareShellScript


class LocalBuilder(Pipeline):
    """A very simple builder that just runs subprocesses in the
    machine where jaci is installed.
    """
    name = 'local-builder'
    steps = [PrepareSSHKey, LocalRetrieve, CheckAndLoadBuildFile, PrepareShellScript, LocalBuild]
