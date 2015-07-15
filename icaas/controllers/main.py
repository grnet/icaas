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


def create_ini_file(url, token, name, p_log, p_url, status):
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

    tmp_str = StringIO.StringIO()
    config.write(tmp_str)
    return tmp_str.getvalue()


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

        user = User.query.filter_by(uuid=astakos['access']['user']['id']).first()
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
def updatebuild(buildid):
    contents = request.get_json()
    if "X-Icaas-Token" not in request.headers:
        abort(401)

    token = request.headers["X-Icaas-Token"]
    if contents:
        status = contents.get("status", None)
        reason = contents.get("reason", None)
        if not status:
            return icass_abort(400, "Field 'status' is missing")
        if status not in ["ERROR", "COMPLETED"]:
            return icass_abort(400, "Bad request: Invalid 'status' field")

        build = Build.query.filter_by(id=buildid, token=token).first()
        if build is None:
            return icass_abort(404, "Build not found")

        build.status = status
        if reason:
            build.erreason = reason

        db.session.commit()
        resp = Response()
        resp.status_code = 200
        return resp

    abort(400)


@main.route('/icaas/<buildid>', methods=['DELETE', 'GET'])
@login_required
def buildview(user, buildid):
    if request.method == 'DELETE':
        build = Build.query.filter_by(id=buildid).first()
        build.deleted = True
        db.session.commit()
        resp = Response()
        resp.status_code = 200
        return resp

    elif request.method == 'GET':
        build = Build.query.filter_by(id=buildid).first()
        if not build:
            return icaas_abort(400, "out")
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

    return icaas_abort(400, "Bad Request")


@main.route('/icaas', methods=['POST'])
@login_required
def post_builds(user):
    token = request.headers["X-Auth-Token"]
    contents = request.get_json()
    if contents:
        name = contents.get("name", None)
        url = contents.get("url", None)
        if not name:
            return icaas_abort(400, "Field 'name' is missing")
        if not url:
            return icaas_abort(400, "Field 'url' is missing")

    p_url = "pithos/" + name + str(datetime.now())
    p_log = "pithos/" + name + str(datetime.now())
    compute_client = cyclades.CycladesComputeClient(settings.COMPUTE_URL,
                                                    token)
    build = Build(user.id, name, url, 0, p_url, p_log)
    db.session.add(build)
    db.session.commit()
    status = settings.ICAAS_ENDPOINT + str(build.id) + "#" + \
             str(build.token)
    person = create_ini_file(url, token, name, p_log, p_url, status)
    prn = []
    prn.append(dict(contents=b64encode(person), path=settings.AGENT_CFG,
               owner='root', group='root', mode=0600))
    prn.append(dict(contents=b64encode("empty"), path=settings.AGENT_INIT,
               owner='root', group='root', mode=0600))
    srv = compute_client.create_server("VM_" + name + str(datetime.now()),
                                       settings.FLAVOR_ID,
                                       settings.IMAGE_ID, personality=prn)
    build.vm_id = srv['id']
    db.session.add(build)
    db.session.commit()
    return jsonify(id=build.id, name=name, url=url)


@main.route('/icaas', methods=['GET'])
@login_required
def get_builds(user):
    builds = Build.query.filter(Build.tenant_id == user.id,
                                Build.deleted == False).all()
    resp = {"builds": []}
    for i in builds:
        resp["builds"].append({"id": i.id, "name": i.name})

    return jsonify(resp)
