FROM debian

# Install Python Setuptools
RUN apt-get update && apt-get install -y python-pip python-dev python-psycopg2

# Bundle app source
ADD . /src

# Install requirements
RUN cd /src && pip install -r requirements.txt

# Initialize app environment
RUN cd /src && python setup.py install
RUN icaas-manage createdb

CMD ["icaas-manage", "runserver", "-h", "0.0.0.0"]
