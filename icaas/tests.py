#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 GRNET S.A.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import logging
import threading

from flask import json
from flask.ext.testing import TestCase
from mock import patch, Mock

import astakosclient

from icaas import create_app, settings
from icaas.models import db, Build, User


logger = logging.getLogger(__name__)

USER_ID = u'9b8d7062-3768-11e5-854b-aa0cf0567195'
USER_TOKEN = u'ukzloztfyvrbwffypayzyymtiinlptwzhgeqmoyw'
VM_ID = '674321'

# Returns an astakosclient response for an successful authorization request
astakos_authorized = Mock(return_value={
    u'access': {
        u'serviceCatalog': [],
        u'token': {
            u'expires': u'2600-09-13T09:18:29.988089+00:00',
            u'id': USER_TOKEN,
            u'tenant': {
                u'id': USER_ID,
                u'name': u'Babis Tereres'}},
        u'user': {
            u'id': USER_ID,
            u'name': u'Babis Tereres',
            u'roles': [
                {u'id': u'5', u'name': u'academic-login-users'},
                {u'id': u'1', u'name': u'default'}],
            u'roles_links': []}}
})

# Returns an astakosclient response for an unsuccessful authorization request
astakos_unauthorized = Mock(
    side_effect=astakosclient.Unauthorized(message='UNAUTHORIZED',
                                           details='invalid token'))

# kamaki Mocks
kamaki_create_server = Mock(return_value={u'id': VM_ID})
kamaki_delete_server = Mock(return_value="")


def create_test_user():
    """Create a test user to be used on the tests"""
    user = User(USER_ID)
    user.token = USER_TOKEN
    db.session.add(user)
    db.session.commit()
    return user


def create_test_build():
    """Create a test build to be used on the tests"""
    user = create_test_user()

    build = Build(
        user.id, "Test Image", "Simple Test Image", False,
        "http://example.org/image.diskdump", 0,
        dict(container='image', object='test.diskdump'),
        dict(container='icaas', object='log.txt'))
    db.session.add(build)
    db.session.commit()
    return (user, build)


class IcaasTestCase(TestCase):
    """ICaaS unittests class"""
    def create_app(self):
        """Create the Flask application"""
        settings.SQLALCHEMY_DATABASE_URI = "sqlite://"

        # monkey patch apply_driver_hacks() method to use StaticPool which
        # shares one connection among all threads. This is needed because
        # sqlite in-memory database ceases to exist as soon as the database
        # connection is closed. Opening 2 database connections (one for each
        # thread) will create two independent in-memory databases. This is
        # fixed in Flask-SQLAlchemy but the patch hasn't reached any stable
        # version yet.
        def sqlite_inmemory_hacks(self, app, info, options):
            pool_size = options.get('pool_size')

            from sqlalchemy.pool import StaticPool
            options['poolclass'] = StaticPool
            if 'connect_args' not in options:
                options['connect_args'] = {}
                options['connect_args']['check_same_thread'] = False

            if pool_size == 0:
                    raise RuntimeError('SQLite in memory database with an '
                                       'empty queue not possible due to data '
                                       'loss.')
            from sqlalchemy.pool import StaticPool
            options['poolclass'] = StaticPool

        import types
        db.apply_driver_hacks = types.MethodType(sqlite_inmemory_hacks, db)

        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        # The preserve context thing is needed when testing.
        # Check : https://github.com/jarus/flask-testing/issues/21
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        return app

    def setUp(self):
        """Setup the application's database"""
        db.create_all()

    def tearDown(self):
        """Remove the application's database"""
        db.session.remove()
        db.drop_all()

    @patch('astakosclient.AstakosClient.authenticate', astakos_authorized)
    def test_authorized(self):
        """Test an authorized access request"""
        rv = self.client.get('/icaas/builds',
                             headers=[('X-Auth-Token', 'test')])
        self.assertEquals(rv.status_code, 200)

    @patch('astakosclient.AstakosClient.authenticate', astakos_unauthorized)
    def test_unauthorized(self):
        """Test an unauthorized access request"""
        rv = self.client.get('/icaas/builds',
                             headers=[('X-Auth-Token', 'test')])
        self.assertEquals(rv.status_code, 401)

    @patch('astakosclient.AstakosClient.authenticate', astakos_authorized)
    @patch('kamaki.clients.cyclades.CycladesComputeClient.create_server',
           kamaki_create_server)
    def test_create_image(self):
        """Test creating a new image"""

        image = dict(account="1ad2898a-5879-11e5-993e-1c6f65d381fb",
                     container='pithos', object='image.diskdump')
        log = dict(container='pithos', object='log')

        data = dict(build=dict(name='PAOK', image=image, log=log,
                    src='http://example.org'))

        rv = self.client.post('/icaas/builds',
                              headers=[('X-Auth-Token', USER_TOKEN)],
                              data=json.dumps(data),
                              content_type='application/json')

        # Wait for the agent creation thread to finish
        for t in threading.enumerate():
            if t.name.startswith('CreateAgentThread'):
                t.join()

        self.assertEquals(json.loads(rv.data)['build']['id'], 1)
        builds = Build.query.all()
        self.assertEquals(len(builds), 1)
        build = builds[0]
        self.assertEquals(build.agent, VM_ID)
        self.assertEquals(build.agent_alive, True)
        self.assertEquals(build.src, 'http://example.org')
        self.assertEquals(json.loads(build.image), image)
        self.assertEquals(json.loads(build.log), log)

    @patch('astakosclient.AstakosClient.authenticate', astakos_authorized)
    @patch('kamaki.clients.cyclades.CycladesComputeClient.delete_server',
           kamaki_delete_server)
    def test_update_build(self):
        """Test updating the build status"""

        user, build = create_test_build()

        rv = self.client.put('/icaas/builds/%d' % build.id,
                             headers=[('X-Icaas-Token', build.token)],
                             data=json.dumps({'status': 'COMPLETED'}),
                             content_type='application/json')

        self.assertEquals(rv.status_code, 204)

        # Wait for the agent destruction thread to finish
        for t in threading.enumerate():
            if t.name.startswith('DestroyAgentThread'):
                t.join()

        rv = self.client.get('/icaas/builds/%d' % build.id,
                             headers=[('X-AUTH-Token', USER_TOKEN)])
        self.assertEquals(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEquals(data['build']['status'], 'COMPLETED')
        self.assertFalse(build.agent_alive)

    def test_update_nonexisting_build(self):
        """Test updating the status of an nonexisting build"""

        create_test_user()

        rv = self.client.put('/icaas/builds/1',
                             headers=[('X-Icaas-Token', 'test')],
                             data=json.dumps({'status': 'COMPLETED'}),
                             content_type='application/json')

        self.assertEquals(rv.status_code, 404)

    @patch('astakosclient.AstakosClient.authenticate', astakos_authorized)
    @patch('kamaki.clients.cyclades.CycladesComputeClient.delete_server',
           kamaki_delete_server)
    def test_delete_build(self):
        """Test deleting an existing build"""
        user, build = create_test_build()

        self.assertFalse(build.deleted)

        rv = self.client.delete('/icaas/builds/%d' % build.id,
                                headers=[('X-AUTH-Token', user.token)])
        self.assertEquals(rv.status_code, 204)
        self.assertTrue(build.deleted)

    @patch('astakosclient.AstakosClient.authenticate', astakos_authorized)
    def test_delete_nonexisting_build(self):
        """Test deleting a nonexisting build"""

        user = create_test_user()
        rv = self.client.delete('/icaas/builds/1',
                                headers=[('X-AUTH-Token', user.token)])
        self.assertEquals(rv.status_code, 404)

# vim: set sta sts=4 shiftwidth=4 sw=4 et ai :
