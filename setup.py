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

from icaas.version import __version__
from pip.download import PipSession
from pip.req import parse_requirements
from setuptools import setup, find_packages
from os.path import dirname, abspath, join

# parse_requirements() returns generator of pip.req.InstallRequirement objects
requirements = join(dirname(abspath(__file__)), 'requirements.txt')
install_reqs = parse_requirements(requirements, session=PipSession())

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='ICaaS',
    version=__version__,
    description='Image Creator as a Service',
    long_description=open('README.md').read(),
    url='https://github.com/grnet/icaas',
    download_url='https://pypi.python.org/pypi/icaas',
    author='Synnefo development team',
    author_email='synnefo-devel@googlegroups.com',
    maintainer='Synnefo development team',
    maintainer_email='synnefo-devel@googlegroups.com',
    license='AGPLv3+',
    packages=find_packages(),
    include_package_data=True,
    install_requires=reqs,
    entry_points={
        'console_scripts': ['icaas-manage = icaas.manage:manager.run']
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU Affero General Public License v3'
        ' or later (AGPLv3+)',
        'Operating System :: POSIX',
        'Programming Language :: Python'
    ],
    keywords='cloud IaaS OS images'
)
# vim: set sta sts=4 shiftwidth=4 sw=4 et ai :
