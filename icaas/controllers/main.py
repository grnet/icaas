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
    abort,
    request,
    jsonify,
    Response,
    Blueprint
)
from functools import wraps

from kamaki.clients import cyclades
from kamaki.clients.utils import https
import astakosclient
from datetime import datetime

from base64 import b64encode
from icaas.models import Build, User, db
from icaas import settings

import ConfigParser
import StringIO

https.patch_with_certs(settings.KAMAKI_SSL_LOCATION)

main = Blueprint('main', __name__)


def create_manifest(url, token, name, p_log, p_url, status):
    config = ConfigParser.ConfigParser()
    config.add_section("service")
    config.add_section("image")
    config.set("image", "url", url)
    config.set("image", "name", name)
    config.set("image", "object", p_url)

    config.set("service", "url", settings.AUTH_URL)
    config.set("service", "token", token)
    config.set("service", "log", p_log)
    config.set("service", "status", status)

    manifest = StringIO.StringIO()
    config.write(manifest)
    return manifest.getvalue()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "X-Auth-Token" not in request.headers:
            abort(403)
        token = request.headers["X-Auth-Token"]
        astakos = astakosclient.AstakosClient(token, settings.AUTH_URL)

        try:
            astakos = astakos.authenticate()
        except astakosclient.errors.Unauthorized:
            abort(401)
        except:
            abort(500)

        uuid = astakos['access']['user']['id']
        user = User.query.filter_by(uuid=uuid).first()
        if not user:
            user = User(astakos['access']['user']['id'])
            user.token = token
            db.session.add(user)
            db.session.commit()
        elif user.token != token:
            user.token = token
            db.session.commit()

        return f(user, *args, **kwargs)
    return decorated_function


def icaas_abort(status_code, message):
    response = jsonify({"badRequest":
                       {'message': message,
                        'code': status_code,
                        'details': ""}})
    response.status_code = status_code
    return response


@main.route('/icaas/<buildid>', methods=['PUT'])
def update(buildid):
    """Update the build status"""
    contents = request.get_json()
    if "X-Icaas-Token" not in request.headers:
        abort(401)

    token = request.headers["X-Icaas-Token"]
    if contents:
        status = contents.get("status", None)
        reason = contents.get("reason", None)
        if not status:
            return icaas_abort(400, "Field 'status' is missing")
        if status not in ["ERROR", "COMPLETED"]:
            return icaas_abort(400, "Bad request: Invalid 'status' field")

        build = Build.query.filter_by(id=buildid, token=token).first()
        if build is None:
            return icaas_abort(404, "Build not found")

        build.status = status
        if reason:
            build.erreason = reason

        db.session.commit()
        response = Response()
        response.status_code = 200
        return response

    abort(400)


@main.route('/icaas/<buildid>', methods=['GET'])
@login_required
def view(user, buildid):
    """View a specific build entry"""
    build = Build.query.filter_by(id=buildid).first()
    if not build:
        return icaas_abort(400, "Build id not valid")

    d = {"id": build.id,
         "name:": build.name,
         "url": build.url,
         "status": build.status,
         "p_url": build.p_url,
         "p_log": build.p_log,
         "created": build.created,
         "updated": build.updated,
         "deleted": build.deleted}

    return jsonify({"build": d})


@main.route('/icaas/<buildid>', methods=['DELETE'])
@login_required
def delete(user, buildid):
    """Delete an existing build entry"""
    build = Build.query.filter_by(id=buildid).first()
    build.deleted = True
    db.session.commit()
    resp = Response()
    resp.status_code = 200
    return resp


@main.route('/icaas', methods=['POST'])
@login_required
def create(user):
    """Create a new image with ICaaS"""
    token = request.headers["X-Auth-Token"]
    contents = request.get_json()
    if contents:
        name = contents.get("name", None)
        url = contents.get("url", None)
        image_container = contents.get("image_container", None)
        log_container = contents.get("log_container", None)

        if not name:
            return icaas_abort(400, "Field 'name' is missing")
        if not url:
            return icaas_abort(400, "Field 'url' is missing")
        if not image_container:
            return icaas_abort(400, "Field 'image_container' is missing")
        if not log_container:
            return icaas_abort(400, "Field 'log_container' is missing")
    else:
        fields = ['name', 'url', 'image_container', 'log_container']
        return icaas_abort(400, 'Required fields: "%s" are missing' %
                                '", "'.join(fields))

    p_url = image_container + "/" + name + str(datetime.now())
    p_log = log_container + "/" + name + str(datetime.now())
    compute_client = cyclades.CycladesComputeClient(settings.COMPUTE_URL,
                                                    token)
    build = Build(user.id, name, url, 0, p_url, p_log)
    db.session.add(build)
    db.session.commit()
    status = settings.ICAAS_ENDPOINT + str(build.id) + "#" + str(build.token)
    manifest = create_manifest(url, token, name, p_log, p_url, status)
    personality = [
        {'contents': b64encode(manifest), 'path': settings.AGENT_CFG,
         'owner': 'root', 'group': 'root', 'mode': 0600},
        {'contents': b64encode("empty"), 'path': settings.AGENT_INIT,
         'owner': 'root', 'group': 'root', 'mode': 0600}]
    srv = compute_client.create_server("VM_" + name + str(datetime.now()),
                                       settings.FLAVOR_ID,
                                       settings.IMAGE_ID,
                                       personality=personality)
    build.vm_id = srv['id']
    db.session.add(build)
    db.session.commit()
    return jsonify(id=build.id, name=name, url=url)


@main.route('/icaas', methods=['GET'])
@login_required
def list_builds(user):
    """List the builds owned by a user"""
    builds = Build.query.filter(Build.tenant_id == user.id,
                                Build.deleted == False).all()  # noqa
    result = [{"id": i.id, "name": i.name} for i in builds]

    return jsonify({"builds": result})

# vim: ai ts=4 sts=4 et sw=4 ft=python
