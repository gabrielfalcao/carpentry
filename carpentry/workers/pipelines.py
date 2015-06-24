#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
from lineup import Pipeline
from carpentry.workers.steps import (
    PrepareSSHKey,
    PushKeyToGithub,
    LocalRetrieve,
    LocalBuild,
    CheckAndLoadBuildFile,
    PrepareShellScript,
)


class LocalBuilder(Pipeline):
    """A very simple builder that just runs subprocesses in the
    machine where carpentry is installed.
    """
    name = 'local-builder'
    steps = [
        PrepareSSHKey,
        PushKeyToGithub,
        LocalRetrieve,
        CheckAndLoadBuildFile,
        PrepareShellScript,
        LocalBuild
    ]
