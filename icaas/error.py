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

"""Module to handle API errors"""

import logging

logger = logging.getLogger(__name__)


class Error(Exception):
    """Implements the Error Exception"""
    status = 400

    def __init__(self, message, status=None, payload=None):
        """Initialize an InvalidUsage instance"""
        super(Error, self).__init__(self)
        self.message = message
        if status is not None:
            self.status = status
        self.payload = payload
        logger.debug("Error: %s" % self.to_dict())

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status'] = self.status
        return rv

# vim: ai ts=4 sts=4 et sw=4 ft=python
