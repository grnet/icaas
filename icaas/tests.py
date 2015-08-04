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

from flask.ext.testing import TestCase
from mock import patch, Mock

import astakosclient

from icaas import create_app, settings
from icaas.models import db


logger = logging.getLogger(__name__)

astakos_authorized = Mock(return_value={
    u'access': {
        u'serviceCatalog': [],
        u'token': {
            u'expires': u'2600-09-13T09:18:29.988089+00:00',
            u'id': u'test',
            u'tenant': {
                u'id': u'9b8d7062-3768-11e5-854b-aa0cf0567195',
                u'name': u'Babis Tereres'}},
        u'user': {
            u'id': u'9b8d7062-3768-11e5-854b-aa0cf0567195',
            u'name': u'Babis Tereres',
            u'roles': [
                {u'id': u'5', u'name': u'academic-login-users'},
                {u'id': u'1', u'name': u'default'}],
            u'roles_links': []}}
})

astakos_unauthorized = Mock(
    side_effect=astakosclient.Unauthorized(message='UNAUTHORIZED',
                                           details='invalid token'))


class IcaasTestCase(TestCase):
    """ICaaS unittests class"""
    def create_app(self):
        settings.SQLALCHEMY_DATABASE_URI = "sqlite://"
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    @patch('astakosclient.AstakosClient.authenticate', astakos_authorized)
    def test_authorized(self):
        rv = self.client.get('/icaas', headers=[('X-Auth-Token', 'test')])
        self.assertEquals(rv.status_code, 200)

    @patch('astakosclient.AstakosClient.authenticate', astakos_unauthorized)
    def test_unauthorized(self):
        rv = self.client.get('/icaas', headers=[('X-Auth-Token', 'test')])
        self.assertEquals(rv.status_code, 401)

# vim: set sta sts=4 shiftwidth=4 sw=4 et ai :
