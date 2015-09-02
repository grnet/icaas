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


from flask import (
    request,
    jsonify,
    Response,
    Blueprint
)

from functools import wraps
from datetime import datetime
from base64 import b64encode
import ConfigParser
import StringIO
import logging

from kamaki.clients import cyclades, ClientError
from kamaki.clients.utils import https

import astakosclient

from icaas.models import Build, User, db
from icaas.error import Error
from icaas.utils import destroy_agent
from icaas import settings

https.patch_with_certs(settings.KAMAKI_SSL_LOCATION)

main = Blueprint('main', __name__)

AGENT_CONFIG = "/etc/icaas/manifest.cfg"
AGENT_INIT = "/.icaas"

logger = logging.getLogger(__name__)


def _build_to_links(build):
    url = "%s%s" % (settings.ENDPOINT, build.id)
    return [{"href": url, "rel": "self"}]


def _build_to_dict(build):
    d = {"id": build.id,
         "name:": build.name,
         "src": build.src,
         "status": build.status,
         "image": build.image,
         "log": build.log,
         "created": build.created,
         "updated": build.updated,
         "deleted": build.deleted,
         "links": _build_to_links(build)}

    return d


def _create_manifest(src, name, log, image, token, buildid, icaas_token):
    """Create manifest file to be injected to the ICaaS Agent VM"""
    config = ConfigParser.ConfigParser()
    config.add_section("service")
    config.add_section("synnefo")
    config.add_section("image")

    config.set("image", "src", src)
    config.set("image", "name", name)
    config.set("image", "object", image)

    config.set("service", "status", "%s%s" % (settings.ENDPOINT, buildid))
    config.set("service", "token", icaas_token)
    config.set("service", "insecure", settings.INSECURE)

    config.set("synnefo", "url", settings.AUTH_URL)
    config.set("synnefo", "token", token)
    config.set("synnefo", "log", log)
    logger.debug("icaas-agent manifest file: %r" % config._sections)

    manifest = StringIO.StringIO()
    config.write(manifest)
    return manifest.getvalue()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.debug('checking X-Auth-Token before function "%s"' % f.__name__)
        if "X-Auth-Token" not in request.headers:
            logger.debug('X-Auth-Token missing')
            raise Error("Token is missing", status=401)
        token = request.headers["X-Auth-Token"]
        astakos = astakosclient.AstakosClient(token, settings.AUTH_URL)

        try:
            astakos = astakos.authenticate()
            logger.debug('X-Auth-Token is valid')
        except astakosclient.errors.Unauthorized:
            logger.debug('X-Auth-Token not valid')
            raise Error("Invalid token", status=401)
        except Exception as e:
            logger.debug("astakosclient raised exception: '%s'" % str(e))
            raise Error("Internal server error", status=500)

        logger.debug('checking if user is present in the database')
        uuid = astakos['access']['user']['id']
        user = User.query.filter_by(uuid=uuid).first()
        if not user:
            user = User(astakos['access']['user']['id'])
            user.token = token
            db.session.add(user)
            db.session.commit()
            logger.debug('added new user %d' % user.id)
        elif user.token != token:
            user.token = token
            db.session.commit()
            logger.debug('update existing user %d' % user.id)
        else:
            logger.debug('user %d found' % user.id)

        return f(user, *args, **kwargs)
    return decorated_function


@main.route('/icaas/<int:buildid>', methods=['PUT'])
def update(buildid):
    """Update the build status"""
    logger.info("update build %d" % buildid)

    if "X-Icaas-Token" not in request.headers:
        raise Error("Missing ICaaS token", status=401)
    token = request.headers["X-Icaas-Token"]

    build = Build.query.filter_by(id=buildid, token=token).first()
    if build is None:
        raise Error("Build not found", status=404)

    params = request.get_json()
    logger.debug("update build %d with params %s" % (buildid, params))
    if params:
        status = params.get("status", None)
        details = params.get("details", None)
        if not status:
            raise Error("Parameter: 'status' is missing", status=400)
        if status not in ["CREATING", "ERROR", "COMPLETED"]:
            raise Error("Invalid 'status' parameter", status=400)

        build.status = status
        if details:
            build.status_details = details
        db.session.commit()

        # Should we delete the agent VM?
        if status == "COMPLETED" or (status == "ERROR" and not settings.DEBUG):
            destroy_agent(build)
        elif status == 'ERROR':
            logger.warning('not deleting the agent VM on errors in debug mode')

        return Response(status=202)

    raise Error("Parameters 'status' and 'status_details' are missing",
                status=400)


@main.route('/icaas/<int:buildid>', methods=['GET'])
@login_required
def view(user, buildid):
    """View a specific build entry"""
    logger.info("view build %d by user %s" % (buildid, user.id))

    build = Build.query.filter_by(id=buildid, user=user.id).first()
    if not build:
        raise Error("Build not found", status=404)

    return jsonify({"build": _build_to_dict(build)})


@main.route('/icaas/<int:buildid>', methods=['DELETE'])
@login_required
def delete(user, buildid):
    """Delete an existing build entry"""
    logger.info("delete buildid %d by user %s" % (buildid, user.id))

    build = Build.query.filter_by(id=buildid, user=user.id).first()
    if not build:
        raise Error("Build not found", status=404)
    build.deleted = True
    db.session.commit()

    return Response(status=200)


@main.route('/icaas', methods=['POST'])
@login_required
def create(user):
    """Create a new image with ICaaS"""
    logger.info("create build by user %s" % user.id)

    token = request.headers["X-Auth-Token"]

    params = request.get_json()
    logger.debug("create build with params %s" % params)
    if params:
        params = params.get("build", None)
    else:
        raise Error('Required field "build" is missing')

    if params:
        missing = "Parameter: '%s' is missing from namespace 'build' or empty"
        invalid = "%s parameter's value not in <container>/<path> format"

        # Image Registration Name
        name = params.get("name", None)
        if not name:
            raise Error(missing % 'name', status=400)
        # User provided Image URL
        src = params.get("src", None)
        if not src:
            raise Error(missing % 'src', status=400)

        # Pithos image object
        image = params.get("image", None)
        if not image:
            raise Error(missing % 'image', status=400)
        separator = image.find('/')
        if separator < 1 or separator == len(image) - 1:
            raise Error(invalid % 'image', status=400)
        # Pithos log object
        log = params.get("log", None)
        if not log:
            raise Error(missing % 'log', status=400)
        separator = log.find('/')
        if separator < 1 or separator == len(image) - 1:
            raise Error(invalid % 'log', status=400)
        # Project to assign the agent VM to
        project = params.get("project", None)
        # Networks of the agent VM
        networks = params.get("networks", None)
    else:
        fields = ['name', 'src', 'image', 'log']
        raise Error('Required fields: "%s" are missing from namespace "build"'
                    % '", "'.join(fields), status=400)

    build = Build(user.id, name, src, None, image, log)
    db.session.add(build)
    db.session.commit()
    logger.debug('created build %r' % build.id)

    manifest = _create_manifest(src, name, log, image, token, build.id,
                                build.token)

    personality = [
        {'contents': b64encode(manifest), 'path': AGENT_CONFIG,
         'owner': 'root', 'group': 'root', 'mode': 0600},
        {'contents': b64encode("empty"), 'path': AGENT_INIT,
         'owner': 'root', 'group': 'root', 'mode': 0600}]

    compute = cyclades.CycladesComputeClient(settings.COMPUTE_URL, token)
    date = datetime.now().strftime('%Y%m%d%H%M%S%f')
    try:
        agent = compute.create_server("icaas-agent-%s-%s" % (build.id, date),
                                      settings.AGENT_IMAGE_FLAVOR_ID,
                                      settings.AGENT_IMAGE_ID,
                                      project_id=project, networks=networks,
                                      personality=personality)
    except ClientError as e:
        build.status = 'ERROR'
        build.status_details = 'icaas agent creation failed'
        db.session.commit()
        logger.error("icaas agent creation failed: (%d, %s)" % (e.status, e))
        raise Error('icaas agent creation failed', e.status,
                    {'details': e.message})
    except Exception as e:
        build.status = 'ERROR'
        build.status_details = 'icaas agent creation failed'
        db.session.commit()
        logger.error("icaas agent creation failed: %s" % e)
        raise Error('Internal Server Error', 500)

    logger.debug("create new icaas agent vm: %s" % agent)
    build.agent = agent['id']
    build.agent_alive = True
    build.status_details = 'started icaas agent creation'
    db.session.commit()

    response = jsonify({"build": _build_to_dict(build)})
    response.status_code = 202
    return response


@main.route('/icaas', methods=['GET'])
@login_required
def list_builds(user):
    """List the builds owned by a user"""
    logger.info('list_builds by user %s' % user.id)

    builds = Build.query.filter(Build.user == user.id,
                                Build.deleted == False).all()  # noqa
    result = [{"links": _build_to_links(i), "id": i.id, "name": i.name} for i
              in builds]

    return jsonify({"builds": result})

# vim: ai ts=4 sts=4 et sw=4 ft=python
