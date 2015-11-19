FROM debian

# Install Python Setuptools
RUN apt-get update && apt-get install -y python-pip python-dev python-psycopg2 --no-install-recommends

# Bundle app source
ADD . /src

WORKDIR /src
# Install requirements
RUN pip install -r requirements.txt
RUN pip install gunicorn

# Initialize app environment
RUN python setup.py install

CMD icaas-manage createdb && gunicorn --config /etc/icaas/gunicorn.conf "icaas:create_app(logfile=None,loglevel='INFO')"
