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
.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
"""

from tvb.basic.config.settings import TVBSettings as cfg
from tvb.core.code_versions.base_classes import UpdateManager
import tvb.core.code_versions.code_update_scripts as code_versions



class CodeUpdateManager(UpdateManager):
    """
    A manager that goes through all the scripts that are newer than the version number 
    written in the .tvb.basic.config.setting configuration file.
    """


    def __init__(self):
        super(CodeUpdateManager, self).__init__(code_versions, cfg.CODE_CHECKED_TO_VERSION, cfg.SVN_VERSION)


    def run_update_script(self, script_name):
        """
        Add specific code after every update script.
        """
        super(CodeUpdateManager, self).run_update_script(script_name)
        # After each update mark the update in cfg file. 
        # In case one update script fails, the ones before will not be repeated.
        cfg.add_entries_to_config_file({cfg.KEY_LAST_CHECKED_CODE_VERSION: script_name.split('_')[0]})


    def run_all_updates(self):
        """
        Upgrade the code to current version. 
        Go through all update scripts with lower SVN version than the current running version.
        """
        file_dict = cfg.read_config_file()
        if file_dict is None or len(file_dict) <= 2:
            ## We've just started with a clean TVB. No need to upgrade anything.
            return

        super(CodeUpdateManager, self).run_all_updates()

        if self.checked_version < self.current_version:
            cfg.add_entries_to_config_file({cfg.KEY_LAST_CHECKED_CODE_VERSION: cfg.SVN_VERSION})
        
        
        
        