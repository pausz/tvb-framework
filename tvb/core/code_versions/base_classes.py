# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and 
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
#
# This program is free software; you can redistribute it and/or modify it under 
# the terms of the GNU General Public License version 2 as published by the Free
# Software Foundation. This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details. You should have received a copy of the GNU General 
# Public License along with this program; if not, you can download it here
# http://www.gnu.org/licenses/old-licenses/gpl-2.0
#
#
#   CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
"""

import os
from tvb.basic.logger.builder import get_logger
from tvb.basic.traits.exceptions import TVBException



class InvalidUpgradeScriptException(TVBException):
    """
    Raised in case an update script is present but does not comply to TVB conventions.
    """


    def __init__(self, message):
        TVBException.__init__(self, message)



class UpdateManager(object):
    """
    An update manager pattern.
    Goes through all the scripts, and based on the current version executed the one in need
    """
    log = get_logger(__name__)


    def __init__(self, module_scripts, check_version, current_version):
        self.update_scripts_module = module_scripts
        self.checked_version = check_version
        self.current_version = current_version


    def get_update_scripts(self, checked_version=None):
        """
        Return all update scripts that need to be executed in order to bring code up to date.
        """
        unprocessed_scripts = []
        if checked_version is None:
            checked_version = self.checked_version

        for file_n in os.listdir(os.path.dirname(self.update_scripts_module.__file__)):
            if '_update' in file_n and file_n.endswith('.py'):
                version_nr = int(file_n.split('_')[0])
                if version_nr > checked_version:
                    unprocessed_scripts.append(file_n)

        result = sorted(unprocessed_scripts, key=lambda x: int(x.split('_')[0]))
        self.log.info("Found unprocessed code update scripts: %s." % result)
        return result


    def run_update_script(self, script_name, **kwargs):
        """
        Run one script file.
        """
        script_module_name = self.update_scripts_module.__name__ + '.' + script_name.split('.')[0]
        script_module = __import__(script_module_name, globals(), locals(), ['update'])

        if not hasattr(script_module, 'update'):
            raise InvalidUpgradeScriptException("Code update scripts should expose a 'update()' method.")

        script_module.update(**kwargs)


    def update_all(self):
        """
        Upgrade the code to current version. 
        """
        if self.checked_version < self.current_version:
            for script_name in self.get_update_scripts():
                self.run_update_script(script_name)
                
        
