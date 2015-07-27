#!/usr/bin/env python

import os
import logging
import sys

from flask.ext.script import Manager, Server
from flask.ext.script.commands import ShowUrls, Clean

from icaas import create_app
from icaas.models import db, User, Build
from icaas.utils import exec_on_timeout, destroy_agent
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


@manager.command
def showsettings():
    """Show current settings"""
    for k,v in settings.__dict__.items():
        if isinstance(k, basestring) and k.isupper():
            print "%s=%s" % (k, v)


@manager.option('-d', '--dry-run', action='store_true',
                help="don't destroy the timed out builds")
@manager.option('-m', help='timeout in minutes [default: 60]', default=60,
                metavar="MINUTES", dest='minutes', type=int)
def timeout(minutes, dry_run):
    """Put in error state all builds that are running for more than
    [MINUTES]
    """

    def set_error(build):
        """Put a build that timed out to error state"""
        if build.status != 'COMPLETED':
            build.status = 'ERROR'
            build.erreason = 'timed out'
            db.session.commit()
        return destroy_agent(build)

    action = (lambda build: True) if dry_run else set_error
    return exec_on_timeout(minutes, action)


if __name__ == "__main__":
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('%(name)s [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    manager.run()

# vim: ai ts=4 sts=4 et sw=4 ft=python
