ICaaS - Image Creator as a Service
==================================

ICaaS is a Python Flask application meant to provide the functionality of
[snf-image-creator](https://www.synnefo.org/docs/snf-image-creator) as a
service, through the use of [Synnefo](https://synnefo.org) VMs.

For the time being, it only works on [Bitnami](https://bitnami.com/) images.

Installation and requirements
-----------------------------

ICaaS uses [SQLAlchemy](http://www.sqlalchemy.org), so ICaaS can support any
[SQL backend supported by SQLAlchemy](http://docs.sqlalchemy.org/en/rel_1_0/core/engines.html#database-urls).
By default it will use a [SQLite](https://www.sqlite.org/) backend.

To install ICaaS (ideally in a virtual env):

```
python setup.py install
```

edit the `icaas/settings/default.py` file to reflect your environment and 
run:

```
icaas-manage createdb
```
to create the database. Then simply launch the service by running:
```
icaas-manage runserver
```

If you prefer to use Docker, you can create your own image, using the provided
Dockerfile:

```
docker build --tag icaas .
docker run -p hostport:5000 icaas
```

