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

from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
from uuid import uuid4

db = SQLAlchemy()


class Build(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(256), unique=False)
    status = db.Column(db.String(32), default="Creating")
    vm_id = db.Column(db.String(128))
    url = db.Column(db.String(256), unique=False)
    p_url = db.Column(db.String(256), unique=False)
    p_log = db.Column(db.String(256), unique=False)
    created = db.Column(db.DateTime, default=datetime.now)
    updated = db.Column(db.DateTime, default=datetime.now,
                        onupdate=datetime.now)
    deleted = db.Column(db.Boolean, default=False)
    erreason = db.Column(db.String(256))
    token = db.Column(db.String(32))

    def __init__(self, tenant_id, name, url, vm_id, p_url, p_log):
        self.tenant_id = tenant_id
        self.name = name
        self.url = url
        self.vm_id = vm_id
        self.p_url = p_url
        self.p_log = p_log
        self.token = str(uuid4()).replace('-', '')

    def __repr__(self):
        return '<Build: id %s, name %s>' % (self.id, self.name)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    uuid = db.Column(db.String(256), unique=True, index=True)
    token = db.Column(db.String(32))

    def __init__(self, uuid):
        self.uuid = uuid

    def __repr__(self):
        return '<Build: id %s, uuid %s>' % (self.id, self.uuid)

# vim: ai ts=4 sts=4 et sw=4 ft=python
