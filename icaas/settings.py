# Flavor ID to use for the ICaaS agent VM
FLAVOR_ID = '1'

# Image ID to use for the ICaaS agent VM
IMAGE_ID = '00000000-0000-0000-0000-00000000000'

# Astakos authentication endpoint
AUTH_URL = 'https://accounts.okeanos.grnet.gr/identity/v2.0'

# Cyclades endpoint
COMPUTE_URL = 'https://cyclades.okeanos.grnet.gr/compute/v2.0'

# Set a really long and random key
SECRET_KEY = '5hh2uo7128pjzv13aqpyx5vvi9j5t75mo6zme88o'

# Cookie name to set for the browser session
SESSION_COOKIE_NAME = 'icaas_session'

SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/test_icaas.db'

# SSL Certificate location
KAMAKI_SSL_LOCATION = '/etc/ssl/certs/ca-certificates.crt'

# Debug mode
DEBUG = True

# ICaaS endpoint URL to be used by the agent VM to update the build status
ICAAS_ENDPOINT = "http://example.org/icaas/"

# ICaaS Agent config file location
AGENT_CFG = "/etc/icaas/manifest.cfg"

# ICaaS Agent init file
AGENT_INIT = "/.icaas"

# vim: ai ts=4 sts=4 et sw=4 ft=python
