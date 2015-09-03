FROM debian

# Install Python Setuptools
RUN apt-get update && apt-get install -y python-pip python-dev python-psycopg2 --no-install-recommends

# Bundle app source
ADD . /src

WORKDIR /src
# Install requirements
RUN pip install -r requirements.txt

# Initialize app environment
RUN python setup.py install
RUN icaas-manage createdb

CMD ["icaas-manage", "runserver", "-h", "0.0.0.0"]
