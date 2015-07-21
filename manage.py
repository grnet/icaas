#!/usr/bin/env python

import os
import logging
import sys

from flask.ext.script import Manager, Server
from flask.ext.script.commands import ShowUrls, Clean

from icaas import create_app
from icaas.models import db, User, Build
from icaas import settings

logger = logging.getLogger()

# default to dev config because no one should use this in
# production anyway
env = os.environ.get('APPNAME_ENV', 'dev')
app = create_app('icaas.settings', env=env)

manager = Manager(app)
manager.add_command("show-urls", ShowUrls())
manager.add_command("clean", Clean())


@manager.shell
def make_shell_context():
    return dict(app=app, db=db, User=User, Build=Build)


@manager.command
def createdb():
    """Creates the ICaaS database"""
    db.create_all()

if __name__ == "__main__":
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('%(name)s [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    manager.run()

# vim: ai ts=4 sts=4 et sw=4 ft=python
