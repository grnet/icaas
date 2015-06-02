FROM debian

# Install Python Setuptools
RUN apt-get update
RUN apt-get install -y python-pip python-dev python-psycopg2

# Add and install Python modules
ADD requirements.txt /src/requirements.txt
RUN cd /src; pip install -r requirements.txt

# Bundle app source
ADD . /src

# Run
CMD ["python", "/src/manage.py", "createdb"]
CMD ["python", "/src/manage.py", "runserver", "-h", "0.0.0.0"]
