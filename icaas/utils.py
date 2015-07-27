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

"""Various handy functions to be used by the ICaaS modules"""

from datetime import datetime, timedelta
import logging

from kamaki.clients import cyclades, ClientError

from icaas.models import Build, User, db
from icaas import settings

logger = logging.getLogger(__name__)


def destroy_agent(build):
    """Destroy the agent associated with a build"""
    logger.info('destroy_agent of build %d' % build.id)

    user = User.query.filter_by(id=build.user).first()
    if not user:
        logger.error('unable to find user %d to delete the agent VM' %
                     build.id)
        return False

    compute = cyclades.CycladesComputeClient(settings.COMPUTE_URL, user.token)
    try:
        compute.delete_server(build.agent)
    except ClientError as e:
        logger.error('failed to delete the icaas agent of build %d: (%d, %s)'
                     % (build.id, e.status, e))
        if e.status == 400:  # The server is probably dead already
            build.agent_alive = False
            db.session.commit()
            return True
        return False

    except Exception as e:
        logger.error('failed to delete the icaas agent of build %d: %s'
                     % (build.id, e))
        return False

    build.agent_alive = False
    db.session.commit()
    return True


def exec_on_timeout(timeout, action):
    """Perform an action on all the builds that have timed out"""

    expiration = datetime.utcnow() - timedelta(minutes=timeout)

    builds = Build.query.filter(Build.created < expiration,
                                Build.agent_alive == True).all()  # noqa

    # Perform the action on all builds that have expired
    for b in builds:
        logger.info("Build %d timed out" % b.id)
        action(b)

# vim: ai ts=4 sts=4 et sw=4 ft=python
