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
    Blueprint,
    copy_current_request_context
)

from functools import wraps
from datetime import datetime, timedelta
from base64 import b64encode
import ConfigParser
import StringIO
import logging
import threading
import json

from kamaki.clients import cyclades, ClientError
from kamaki.clients.utils import https

import astakosclient

from icaas.models import Build, User, db
from icaas.error import Error
from icaas.utils import destroy_agent
from icaas import settings

https.patch_with_certs(settings.KAMAKI_SSL_LOCATION)

builds = Blueprint('builds', __name__)

AGENT_CONFIG = "/etc/icaas/manifest.cfg"
AGENT_INIT = "/.icaas"

logger = logging.getLogger(__name__)


def _build_to_links(build):
    url = "%s/%s" % (settings.ENDPOINT, build.id)
    return [{"href": url, "rel": "self"}]


def _update_status_details(build, params):
    details = build.status_details
    details = json.loads(details) if details else {}
    curtask = params.get('details', None)
    if curtask:
        details['details'] = curtask
    agent_progress = params.get("agent-progress", None)
    if agent_progress:
        try:
            details['agent-progress'] = {
                'current': int(agent_progress['current']),
                'total': int(agent_progress['total'])}
        except (ValueError, KeyError, TypeError) as e:
            logger.warning("Failed to parse 'agent-progress' with error '%s'",
                           str(e))
            raise Error("Malformed status details", status=400)

    build.status_details = json.dumps(details)


def _build_to_dict(build):
    d = {"id": build.id,
         "name": build.name,
         "src": build.src,
         "description": build.description,
         "public": build.public,
         "status": build.status,
         "status_details": build.status_details,
         "image": json.loads(build.image),
         "log": json.loads(build.log),
         "created": build.created,
         "updated": build.updated,
         "links": _build_to_links(build)}

    return d


def _create_manifest(build, token):
    """Create manifest to be send to the ICaaS Agent VM"""

    image = json.loads(build.image)
    log = json.loads(build.log)

    manifest = {}

    manifest['progress'] = {'heuristic': settings.PROGRESS_HEURISTIC,
                            'interval': settings.PROGRESS_INTERVAL}

    manifest['image'] = {'src': build.src,
                         'name': build.name,
                         'container': image['container'],
                         'object': image['object']}

    if 'account' in image:
        manifest['image']['account'] = image['account']
    if build.public:
        # All booleans should be made to strings for backwards compatibility.
        # The agent may expect to find the manifest, either on the disk or by
        # doing an API call and the ConfigParser that creates the file,
        # converts everything to strings.
        manifest['image']['public'] = str(True)
    if len(build.description):
        manifest['image']['description'] = build.description

    manifest['service'] = {'status': '%s/builds/agent/%s' %
                                     (settings.ENDPOINT, build.id),
                           'token': build.token,
                           'insecure': str(settings.INSECURE)}
    manifest['synnefo'] = {'url': settings.AUTH_URL,
                           'token': token}
    manifest['log'] = {'container': log['container'],
                       'object': log['object']}

    if "account" in log and log["account"]:
        manifest['log']['account'] = log['account']

    logger.debug("icaas-agent manifest : %r" % manifest)

    return manifest


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


@builds.route('/icaas/builds/agent/<int:buildid>/<nonce>', methods=['GET'])
def agent_manifest(buildid, nonce):
    """Send manifest to the agent"""
    logger.info("manifest for build %d with nonce %s requested" %
                (buildid, nonce))

    build = Build.query.filter_by(id=buildid, nonce=nonce,
                                  deleted=False).first()  # noqa
    if build is None:
        raise Error("Manifest retrieval is forbidden", status=403)

    if build.nonce_invalid:
        logger.warning("Manifest retrieval requested again for build: %d" %
                       buildid)
        raise Error("Manifest retrieval is forbidden", status=403)

    user = User.query.filter_by(id=build.user).first()
    if not user:
        # This should never happen
        logger.error("Unknown user: %d for build %d", (build.user, build.id))

    now = datetime.utcnow()
    expires = build.created + timedelta(minutes=settings.MANIFEST_TIMEOUT)
    if expires < now:
        logger.warning("Manifest retrieval expired!")
        build.nonce_invalid = True
        build.status = 'ERROR'
        build.details = 'Agent start up expired'
        db.session.commit()

        @copy_current_request_context
        def destroy_agent_wrapper():
            """Thread that will kill the agent VM"""
            build = Build.query.filter_by(id=buildid).first()
            if build is None:
                # Normally this cannot happen
                logger.error('Build with id=%d not found!' % build.id)
                return
            destroy_agent(build)

        if not settings.DEBUG:
            thread = threading.Thread(target=destroy_agent_wrapper,
                                      name="DestroyAgentThread-%d" % build.id)
            thread.daemon = False
            thread.start()
        else:
            logger.warning('not deleting the agent VM on errors in debug mode')
        raise Error("Manifest retrieval expired", status=403)

    if not build.is_active():
        raise Error("Build is not active", status=403)

    build.nonce_invalid = True
    _update_status_details(build, {'details': "Agent booted normally"})
    db.session.commit()

    return jsonify({"manifest": _create_manifest(build, user.token)})


@builds.route('/icaas/builds/agent/<int:buildid>', methods=['PUT'])
def agent_update(buildid):
    """Update the build status. Only to be used by the ICaaS agent."""
    logger.info("update build %d by agent" % buildid)

    if "X-Icaas-Token" not in request.headers:
        raise Error("Missing ICaaS token", status=401)
    token = request.headers["X-Icaas-Token"]

    build = Build.query.filter_by(id=buildid, token=token,
                                  deleted=False).first()  # noqa
    if build is None:
        raise Error("Build not found", status=404)

    params = request.get_json()
    logger.debug("update build %d by agent with params %s" % (buildid, params))
    if params:
        status = params.get("status", None)

        if not status:
            raise Error("Parameter: 'status' is missing", status=400)
        if status not in build.get_status_types():
            raise Error("Parameter: 'status' is not valid", status=400)

        # Updating a build which is in a finished state is not allowed
        if not build.is_active():
            raise Error('Build is not active', status=403)

        if status == 'CANCELED':
            raise Error('Agent cannot cancel a build', status=403)

        build.status = status

        _update_status_details(build, params)
        db.session.commit()

        # Should we delete the agent VM?
        if status == "COMPLETED" or (status == "ERROR" and not settings.DEBUG):

            @copy_current_request_context
            def destroy_agent_wrapper():
                """Thread that will kill the agent VM"""
                # Check create_agent() to see why we are doing this
                build = Build.query.filter_by(id=buildid).first()
                if build is None:
                    # Normally this cannot happen
                    logger.error('Build with id=%d not found!' % build.id)
                    return
                destroy_agent(build)

            thread = threading.Thread(target=destroy_agent_wrapper,
                                      name="DestroyAgentThread-%d" % build.id)
            thread.daemon = False
            thread.start()
        elif status == 'ERROR':
            logger.warning('not deleting the agent VM on errors in debug mode')

        return Response(status=204)

    raise Error("Parameters 'status' and 'status_details' are missing",
                status=400)


@builds.route('/icaas/builds/<int:buildid>', methods=['PUT'])
@login_required
def update(user, buildid):
    """Update the build status"""
    logger.info("update the build %d status by user %s" % (buildid, user.id))

    build = Build.query.filter_by(id=buildid, user=user.id,
                                  deleted=False).first()  # noqa
    if not build:
        raise Error("Build not found", status=404)

    params = request.get_json()
    logger.debug("update build %d with params %s" % (buildid, params))

    if not params:
        raise Error("Parameter: 'action' is missing", status=400)

    # Check if action was provided
    action = params.get('action', 'None')
    if action is None:
        raise Error("Parameter: 'action' is missing", status=400)

    if action.lower() != 'cancel':
        raise Error('Invalid action', status=400)

    if not build.is_active():
        raise Error("Build is not active", status=403)

    build.status = 'CANCELED'
    _update_status_details(build, {'details': "Canceled by the user"})
    db.session.commit()

    @copy_current_request_context
    def destroy_agent_wrapper():
        """Thread that will kill the agent VM"""
        # Check create_agent() to see why we are doing this
        build = Build.query.filter_by(id=buildid).first()
        if build is None:
            # Normally this cannot happen
            logger.error('Build with id=%d not found!' % build.id)
            return
        destroy_agent(build)

    thread = threading.Thread(target=destroy_agent_wrapper,
                              name="DestroyAgentThread-%d" % build.id)
    thread.daemon = False
    thread.start()

    return Response(status=204)


@builds.route('/icaas/builds/<int:buildid>', methods=['GET'])
@login_required
def view(user, buildid):
    """View a specific build entry"""
    logger.info("view build %d by user %s" % (buildid, user.id))

    build = Build.query.filter_by(id=buildid, user=user.id,
                                  deleted=False).first()  # noqa
    if not build:
        raise Error("Build not found", status=404)

    return jsonify({"build": _build_to_dict(build)})


@builds.route('/icaas/builds/<int:buildid>', methods=['DELETE'])
@login_required
def delete(user, buildid):
    """Delete an existing build entry"""
    logger.info("delete buildid %d by user %s" % (buildid, user.id))

    build = Build.query.filter_by(id=buildid, user=user.id,
                                  deleted=False).first()  # noqa
    if not build:
        raise Error("Build not found", status=404)
    build.deleted = True
    db.session.commit()

    buildid = build.id

    @copy_current_request_context
    def destroy_agent_wrapper():
        """Thread that will kill the agent VM"""
        # Check create_agent() to see why we are doing this
        build = Build.query.filter_by(id=buildid).first()
        if build is None:
            # Normally this cannot happen
            logger.error('Build with id=%d not found!' % build.id)
            return
        destroy_agent(build)

    if build.agent_alive:
        thread = threading.Thread(target=destroy_agent_wrapper,
                                  name="DestroyAgentThread-%d" % build.id)
        thread.daemon = False
        thread.start()

    return Response(status=204)


@builds.route('/icaas/builds', methods=['POST'])
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

        # Image Registration Name
        name = params.get("name", None)
        if not name:
            raise Error(missing % 'name', status=400)
        # User provided Image URL
        src = params.get("src", None)
        if not src:
            raise Error(missing % 'src', status=400)

        def check_dict_fields(name, value, fields):
            if not value:
                raise Error(missing % name, status=400)
            if type(value) != dict:
                raise Error('"%s" parameter is not a dictionary' % name,
                            status=400)
            for f in fields:
                if f not in value:
                    raise Error('"%s" field missing from parameter: "%s"' %
                                (f, name), status=400)
        # Pithos image object
        image = params.get("image", None)
        check_dict_fields('image', image, ('container', 'object'))

        # Pithos log object
        log = params.get("log", None)
        check_dict_fields('log', log, ('container', 'object'))

        # Image description
        descr = params.get("description", None)

        # Is the image public?
        public = params.get("public", False)

        # Project to assign the agent VM to
        project = params.get("project", None)
        # Networks of the agent VM
        networks = params.get("networks", None)
    else:
        fields = ['name', 'src', 'image', 'log']
        raise Error('Required fields: "%s" are missing from namespace "build"'
                    % '", "'.join(fields), status=400)

    build = Build(user.id, name, descr, public, src, None, image, log)
    _update_status_details(build, {'details': "Build request accepted"})
    db.session.add(build)
    db.session.commit()
    logger.debug('created build %r' % build.id)

    # Check comment below to see why we are doing this
    buildid = build.id

    @copy_current_request_context
    def create_agent():
        """Create ICaaS agent VM"""

        # This is needed because the original build object is attached to the
        # session of the father thread and any changes made to it from this
        # thread won't be committed to the database using db.session.commit()
        build = Build.query.filter_by(id=buildid,
                                      deleted=False).first()  # noqa
        if build is None:
            # Normally this cannot happen
            logger.error('Build with id=%d not found!' % build.id)
            return

        # Create the manifest URL
        config = ConfigParser.ConfigParser()
        config.add_section("manifest")
        config.set("manifest", "url", "%s/builds/agent/%d/%s" %
                   (settings.ENDPOINT, build.id, build.nonce))
        manifest = StringIO.StringIO()
        config.write(manifest)

        personality = [
            {'contents': b64encode(manifest.getvalue()), 'path': AGENT_CONFIG,
             'owner': 'root', 'group': 'root', 'mode': 0600},
            {'contents': b64encode("empty"), 'path': AGENT_INIT,
             'owner': 'root', 'group': 'root', 'mode': 0600}]

        compute = cyclades.CycladesComputeClient(settings.COMPUTE_URL, token)
        date = datetime.now().strftime('%Y%m%d%H%M%S%f')
        try:
            agent = compute.create_server("icaas-agent-%s-%s" %
                                          (build.id, date),
                                          settings.AGENT_IMAGE_FLAVOR_ID,
                                          settings.AGENT_IMAGE_ID,
                                          project_id=project,
                                          networks=networks,
                                          personality=personality)
        except ClientError as e:
            build.status = 'ERROR'
            msg = "icaas agent creation failed: (%d, %s)" % (e.status, e)
            _update_status_details(build, {'details': msg})
            db.session.commit()
            logger.error("icaas agent creation failed: (%d, %s)"
                         % (e.status, e))
            return
        except Exception as e:
            build.status = 'ERROR'
            params = {'details': "icaas agent creation failed"}
            _update_status_details(build, params)
            db.session.commit()
            logger.error("icaas agent creation failed: %s" % e)
            return

        logger.debug("create new icaas agent vm: %s" % agent)
        build.agent = agent['id']
        build.agent_alive = True
        params = {'details': "started icaas agent creation"}
        _update_status_details(build, params)
        db.session.commit()

    thread = threading.Thread(target=create_agent,
                              name="CreateAgentThread-%d" % build.id)
    thread.daemon = False

    response = jsonify({"build": _build_to_dict(build)})
    response.status_code = 202

    thread.start()
    return response


@builds.route('/icaas/builds', methods=['GET'])
@login_required
def list_builds(user):
    """List the builds owned by a user"""
    logger.info('list_builds by user %s' % user.id)

    # Check if status was provided
    status = request.args.get('status')

    # Check if details was provided
    details = request.args.get('details', '0')

    if not status:
        blds = Build.query.filter_by(user=user.id, deleted=False).all()  # noqa
    elif status.upper() in ('CREATING', 'ERROR', 'COMPLETED'):
        blds = Build.query.filter_by(user=user.id, deleted=False,
                                     status=status.upper()).all()  # noqa
    else:
        raise Error("Invalid value for parameter 'status'. Valid values are: "
                    "'CREATING', 'ERROR', 'COMPLETED'")

    if details == '0':
        result = [{"links": _build_to_links(b), "id": b.id, "name": b.name}
                  for b in blds]
    elif details == '1':
        result = [_build_to_dict(b) for b in blds]
    else:
        raise Error("Invalid value for parameter 'details'. Valid values are: "
                    "'0' and '1'")

    return jsonify({"builds": result})

# vim: ai ts=4 sts=4 et sw=4 ft=python
