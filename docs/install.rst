.. _installation:

Installation
^^^^^^^^^^^^

Installation using Docker
-------------------------

This guide is written for a Debian -or Debian derived distribution- machine,
that has `Docker <https://www.docker.com/>`_ installed.

You can build the Docker Image yourself, using the latest source:

.. code-block:: console

    # git clone https://github.com/grnet/icaas
    # docker build -t icaas icaas

The ICaaS Docker Image uses `Gunicorn <http://gunicorn.org/>`_ to serve the application. A
proper web server should handle and forward requests to Gunicorn. We'll
install Nginx on the host as an example, but the same setup can be achieved
using Nginx inside another container.

.. code-block:: console

    # apt-get install nginx

Now edit ``/etc/nginx/site-available/default`` so it contains:

.. code-block:: console

    server {
      listen 80;
      server_name icaas.example.org;

      ssl on;
      ssl_certificate /path/to/your/certificate.crt;
      ssl_certificate_key /path/to/your/key.pem;

      location /icaas {
        proxy_set_header        Host $host;
        proxy_set_header        X-Real-IP $remote_addr;
        proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header        X-Forwarded-Proto $scheme;
        proxy_redirect          http:// https://;
        proxy_pass              http://127.0.0.1:8080;
      }
    }

Remember to change ``server_name``, ``ssl_certificate`` and
``ssl_certificate_key`` according to your setup.

ICaaS needs a Postgresql database to store its data. To start a container
using the latest Postgres Docker Image, run:

.. code-block:: console

    # docker run --name icaas-postgres -e POSTGRES_PASSWORD=postgresqlpassword -d postgres

For more information on how to use the Postgres Docker Image, consult the
`official docs <https://hub.docker.com/_/postgres/>`_.

To configure the ICaaS service, create a file called ``icaas.config`` and add
the following:

.. code-block:: console

    ICAAS_AGENT_IMAGE_FLAVOR_ID=1111
    ICAAS_AUTH_URL=https://accounts.example.org/identity/v2.0
    ICAAS_COMPUTE_URL=https://compute.example.org/compute/v2.0
    ICAAS_ENDPOINT=http://icaas.example.org/icaas
    ICAAS_AGENT_IMAGE_ID=11111111-1111-1111-1111-111111111111
    ICAAS_SECRET_KEY=RANDOM_STRING_THAT_YOU_NEED_TO_CHANGE
    ICAAS_SQLALCHEMY_DATABASE_URI=postgres://postgres:postgresqlpassword@database/postgres

There are the minimum settings that the ICaaS service needs. The complete list
of all settings and their description is located `here <https://github.com/grnet/icaas/blob/master/icaas/settings/default.py>`_.
Since we're using Docker to run the service, we're passing the settings as
enviroment variables to the service. ICaaS will search for env variables
starting with ``ICAAS_``, so, ``AUTH_URL`` becomes ``ICAAS_AUTH_URL`` and so on.

To configure gunicorn create a file, e.g., ``/etc/gunicorn-icaas.conf``,  containing the following:

.. code-block:: console

    bind = "0.0.0.0:8080"
    workers = 4
    log-level = "info"
    accesslog = "-"
    errorlog = "-"
    timeout = 43200

Finally, to start the ICaaS service, run:

.. code-block:: console

    # docker run --link icaas-postgres:database --env-file icaas.config -d --restart=always -p 127.0.0.1:8080:8080 -v /etc/gunicorn-icaas.conf:/etc/icaas/gunicorn.conf:ro icaas
