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
from base64 import urlsafe_b64encode as b64encode


import json

db = SQLAlchemy()


class Build(db.Model):
    """Represents the Build model"""
    __tablename__ = 'build'
    # Unique build ID
    id = db.Column(db.Integer, primary_key=True, index=True)
    # User ID
    user = db.Column(db.Integer, db.ForeignKey('user.id'))
    # Image Registration Name
    name = db.Column(db.String(256))
    # Image description
    description = db.Column(db.String(256), default="")
    # Is the image public?
    public = db.Column(db.Boolean)
    # Build status
    status = db.Column(db.Enum('CREATING', 'ERROR', 'COMPLETED', 'CANCELED',
                               name='status_types'),
                       default="CREATING", index=True)
    # ID of the ICaaS agent VM
    agent = db.Column(db.String(128))
    # Is the ICaaS agent alive?
    agent_alive = db.Column(db.Boolean, default=False)
    # User Provided Image URL
    src = db.Column(db.String(256))
    # Pithos Image Object
    image = db.Column(db.String(256))
    # ICaaS creation log in Pithos
    log = db.Column(db.String(256))
    # Build creation time
    created = db.Column(db.DateTime, default=datetime.utcnow)
    # Build update time
    updated = db.Column(db.DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    # Is the build deleted?
    deleted = db.Column(db.Boolean, default=False, index=True)
    # Detailed description of the current status
    status_details = db.Column(db.String(256),
                               default="build request accepted")
    # ICaaS session token
    token = db.Column(db.String(32))

    # ICaaS agent communication nonce
    nonce = db.Column(db.String(64), unique=True)

    # Has the nonce been invalidated?
    nonce_invalid = db.Column(db.Boolean, default=False)

    # Index to be used to check if the agent VM timed out
    __table_args__ = (db.Index('agent_alive_index', 'agent_alive', 'created'),)

    def __init__(self, user, name, descr, public, src, agent, image, log):
        """Initialize a Build object"""

        assert type(image) == dict
        assert type(log) == dict

        self.user = user
        self.name = name
        self.description = descr
        self.public = public
        self.src = src
        self.agent = agent
        self.image = json.dumps(image)
        self.log = json.dumps(log)
        self.token = str(uuid4()).replace('-', '')
        self.nonce = b64encode(uuid4().bytes + uuid4().bytes).strip('=')

    def is_active(self):
        """Returns True if the build has not finished yet"""
        return self.status == 'CREATING'

    @classmethod
    def get_status_types(cls):
        """Returns the list of valid status types"""
        return cls.status.property.columns[0].type.enums

    def __repr__(self):
        return '<Build: id %s, name %s>' % (self.id, self.name)


class User(db.Model):
    """Represents the User model"""
    __tablename__ = 'user'
    # Unique User ID
    id = db.Column(db.Integer, primary_key=True, index=True)
    # Synnefo UUID of the User
    uuid = db.Column(db.String(256), unique=True, index=True)
    # Synnefo User token
    token = db.Column(db.String(64))

    def __init__(self, uuid):
        """Initialize a User object"""
        self.uuid = uuid

    def __repr__(self):
        return '<Build: id %s, uuid %s>' % (self.id, self.uuid)

# vim: ai ts=4 sts=4 et sw=4 ft=python
