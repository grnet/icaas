# Flavor ID to use for the host VM
FLAVOR_ID = '42'

# Image ID to use for the host VM
IMAGE_ID = 'b1acb3fe-0496-4510-867c-4cf5f33b196d'

# Astakos authentication endpoint
AUTH_URL = 'https://accounts.okeanos.grnet.gr/identity/v2.0'

# Cyclades endpoint
COMPUTE_URL = 'https://cyclades.okeanos.grnet.gr/compute/v2.0'

# Set a really long and random key
SECRET_KEY = 'qqqqqqaaaaaazzzzz'

# Cookie name to set for the browser session
SESSION_COOKIE_NAME = 'icaas_session'

SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/test_icaas.db'

# SSL Certificate location
KAMAKI_SSL_LOCATION = '/etc/ssl/certs/ca-certificates.crt'

# Debug mode
DEBUG = True

# ICaaS endpoint URL
ICAAS_ENDPOINT = "http://host:port/icaas/"

# ICaaS Agent config file locaiton
AGENT_CFG = "/etc/icaas/manifest.cfg"

# ICaaS Agent init file
AGENT_INIT = "/.icaas"
