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

"""Module hosting the settings for the ICaaS service. All other ICaaS
modules access the settings by importing this one.
"""

import os
import sys

# import the default settings
from icaas.settings.default import *  # noqa

CONFIG = os.environ.get('ICAAS_CONFIG', '/etc/icaas.conf')
if os.path.exists(CONFIG):
    try:
        execfile(CONFIG)
    except Exception as e:
        sys.stderr.write('Failed to read settings file: %s. Reason: %r\n'
                         % (CONFIG, e))
        raise SystemExit(1)

# Overwrite the value of a setting if the environment variable
# ICAAS_SETTINGNAME is defined.
for i in [var for var in os.environ if var.startswith("ICAAS_")]:
    setattr(sys.modules[__name__], i[6:], os.environ[i])

# vim: ai ts=4 sts=4 et sw=4 ft=python
