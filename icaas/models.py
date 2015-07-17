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
    """Represents the Build model"""
    # Unique build ID
    id = db.Column(db.Integer, primary_key=True, index=True)
    # User ID
    user = db.Column(db.Integer, db.ForeignKey('user.id'))
    # Image Registration Name
    name = db.Column(db.String(256), unique=False)
    # Build status (Creating|Completed|Error)
    status = db.Column(db.String(32), default="Creating")
    # ID of the ICaaS agent VM
    vm = db.Column(db.String(128))
    # User Provided Image URL
    src = db.Column(db.String(256), unique=False)
    # Pithos Image Object
    image = db.Column(db.String(256), unique=False)
    # ICaaS creation log in Pithos
    log = db.Column(db.String(256), unique=False)
    # Build creation time
    created = db.Column(db.DateTime, default=datetime.now)
    # Build update time
    updated = db.Column(db.DateTime, default=datetime.now,
                        onupdate=datetime.now)
    # Is the build deleted?
    deleted = db.Column(db.Boolean, default=False)
    # Reason of Error
    erreason = db.Column(db.String(256))
    # ICaaS session token
    token = db.Column(db.String(32))

    def __init__(self, user, name, src, vm, image, log):
        """Initialize a Build object"""
        self.user = user
        self.name = name
        self.src = src
        self.vm = vm
        self.image = image
        self.log = log
        self.token = str(uuid4()).replace('-', '')

    def __repr__(self):
        return '<Build: id %s, name %s>' % (self.id, self.name)


class User(db.Model):
    """Represents the User model"""
    # Unique User ID
    id = db.Column(db.Integer, primary_key=True, index=True)
    # Synnefo UUID of the User
    uuid = db.Column(db.String(256), unique=True, index=True)
    # Synnefo User token
    token = db.Column(db.String(32))

    def __init__(self, uuid):
        """Initialize a User object"""
        self.uuid = uuid

    def __repr__(self):
        return '<Build: id %s, uuid %s>' % (self.id, self.uuid)

# vim: ai ts=4 sts=4 et sw=4 ft=python
