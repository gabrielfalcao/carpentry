# -*- coding: utf-8 -*-
#
import re
# import uuid
# import bcrypt
# import logging
# from dateutil.parser import parse as parse_datetime
# from datetime import datetime
from cqlengine import columns
from cqlengine.models import Model
# from jaci.server import get_absolute_url


def slugify(string):
    return re.sub(r'\W+', '', string)


class Builder(Model):
    id = columns.TimeUUID(primary_key=True, partition_key=True)
    name = columns.Text(required=True)
    git_url = columns.Text(index=True)
    shell_script = columns.Text(required=True)
    id_rsa_private = columns.Text()
    id_rsa_public = columns.Text()
    status = columns.Text(default='ready')

    def to_dict(self):
        return dict(self.items())


class JaciPreference(Model):
    id = columns.TimeUUID(primary_key=True, partition_key=True)
    key = columns.Text(required=True)
    value = columns.Text(required=True)

    def to_dict(self):
        return dict(self.items())


class Build(object):
    pass
