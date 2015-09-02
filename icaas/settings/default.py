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

"""Module hosting the default settings for the ICaaS service"""

# Flavor ID to use for the ICaaS agent VM
AGENT_IMAGE_FLAVOR_ID = '1'

# Image ID to use for the ICaaS agent VM
AGENT_IMAGE_ID = '00000000-0000-0000-0000-00000000000'

# Astakos authentication endpoint
AUTH_URL = 'https://accounts.okeanos.grnet.gr/identity/v2.0'

# Cyclades endpoint
COMPUTE_URL = 'https://cyclades.okeanos.grnet.gr/compute/v2.0'

# Set a really long and random key
SECRET_KEY = '5hh2uo7128pjzv13aqpyx5vvi9j5t75mo6zme88o'

# Cookie name to set for the browser session
SESSION_COOKIE_NAME = 'icaas_session'

# Service Database
SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/icaas.db'

# SSL Certificate location
KAMAKI_SSL_LOCATION = '/etc/ssl/certs/ca-certificates.crt'

# Debug mode
DEBUG = True

# ICaaS endpoint URL to be used by the agent VM to update the build status
ENDPOINT = "http://example.org/icaas/"

# This options allows the ICaaS agent to perform "insecure" SSL connections
# when communicating with the ICaaS service through the endpoint URL
INSECURE = False

# vim: ai ts=4 sts=4 et sw=4 ft=python
