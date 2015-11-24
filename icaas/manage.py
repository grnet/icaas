#!/usr/bin/env python

import logging
import unittest

from flask.ext.script import Manager
from flask.ext.script.commands import ShowUrls, Clean

from icaas import settings
from icaas import create_app
from icaas.models import db, User, Build
from icaas.utils import exec_on_timeout, destroy_agent

manager = Manager(create_app)
manager.add_command("showurls", ShowUrls())
manager.add_command("clean", Clean())
manager.add_option('--log-file', metavar="FILE", dest='logfile', default=None,
                   help="Write to this log file [%(default)s]")
manager.add_option('--log-format', metavar="STRING", dest='logformat',
                   help='Set the log format')
manager.add_option('--log-config', metavar="FILE", dest='logconfig',
                   help="Set the log config file to use [%(default)s]",
                   default=None)
manager.add_option('--log-level', metavar="LEVEL", dest='loglevel',
                   help="Set the log level threshold [WARNING]",
                   default=logging.WARNING)


@manager.shell
def make_shell_context():
    return dict(app=manager.app, db=db, User=User, Build=Build)


@manager.command
def createdb():
    """Creates the ICaaS database"""
    db.create_all()


@manager.option('-t', '--test-case', action='append', dest='names',
                help='Run specific test cases', type=str)
@manager.option('-s', '--show-tests', action='store_true', dest='show',
                default=False,
                help='Show the name of the tests without running them')
def test(names, show):
    """Run tests"""
    loader = unittest.TestLoader()
    if not names:
        tests = loader.loadTestsFromName('icaas.tests.IcaasTestCase')
    else:
        tests = unittest.TestSuite()
        for n in names:
            tests.addTests(loader.loadTestsFromName(
                           'icaas.tests.IcaasTestCase.%s' % n))
    if show:
        for t in tests:
            print t
    else:
        unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def showsettings():
    """Show current settings"""
    for k, v in settings.__dict__.items():
        if isinstance(k, basestring) and k.isupper():
            print "%s=%s" % (k, v)


@manager.option('-d', '--dry-run', action='store_true',
                help="don't destroy the timed out builds")
@manager.option('-m', help='timeout period in minutes [%(default)d]',
                default=settings.AGENT_TIMEOUT, metavar="MINUTES",
                dest='minutes', type=int)
def timeout(minutes, dry_run):
    """Put in error state all builds that are running for more than a specific
    period of time
    """

    def set_error(build):
        """Put a build that timed out to error state"""
        if build.status != 'COMPLETED':
            build.status = 'ERROR'
            build.status_details = 'timed out'
            db.session.commit()
        return destroy_agent(build)

    action = (lambda build: True) if dry_run else set_error
    return exec_on_timeout(minutes, action)


if __name__ == "__main__":
    manager.run()

# vim: ai ts=4 sts=4 et sw=4 ft=python
