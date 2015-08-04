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

import sys
import logging

from flask import Flask, jsonify

from icaas.version import __version__
from icaas.models import db
from icaas.controllers.main import main
from icaas.error import Error
from icaas import settings


logger = logging.getLogger()


def create_app(**kwargs):

    app = Flask(__name__)
    app.version = __version__
    app.config.from_object(settings)

    if 'logfile' in kwargs:
        if kwargs['logfile'] is None:
            handler = logging.StreamHandler(sys.stderr)
        else:
            handler = logging.FileHandler(kwargs['logfile'])

        if kwargs['logformat'] is not None:
            formatter = logging.Formatter(kwargs['logformat'])
            handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.setLevel(kwargs['loglevel'])

    if 'logconfig' in kwargs:
        if kwargs['logconfig'] is not None:
            logging.config.fileConfig(kwargs['logconfig'])

    # initialize SQLAlchemy
    db.init_app(app)

    # Override the default error handler
    @app.errorhandler(Error)
    def handle_invalid_usage(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status
        return response

    # register our blueprints
    app.register_blueprint(main)

    return app

# vim: ai ts=4 sts=4 et sw=4 ft=python
