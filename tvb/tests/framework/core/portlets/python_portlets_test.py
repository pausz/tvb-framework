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
Created on Apr 27, 2012

.. moduleauthor:: bogdan.neacsa <bogdan.neacsa@codemart.ro>
"""
import os
import unittest
from tvb.core.entities import model
from tvb.basic.config.settings import TVBSettings as cfg
from tvb.core.entities.storage import dao
from tvb.core.entities.file.files_helper import FilesHelper
from tvb.core.portlets.portlet_configurer import PortletConfigurer
from tvb.tests.framework.core.base_testcase import TransactionalTestCase


class PythonPortletsTest(TransactionalTestCase):
    
    
    def setUp(self):
        """
        Sets up the environment for testing;
        creates a test user, a test project and saves config file
        """
#        self.clean_database()
        user = model.User("test_user", "test_pass", "test_mail@tvb.org", True, "user")
        self.test_user = dao.store_entity(user) 
        project = model.Project("test_proj", self.test_user.id, "description")
        self.test_project = dao.store_entity(project) 
        import tvb.tests.framework
        self.old_config_file = cfg.CURRENT_DIR
        cfg.CURRENT_DIR = os.path.dirname(tvb.tests.framework.__file__)
        
        
    def tearDown(self):
        """
        Remove project folders and restore config file
        """
        FilesHelper().remove_project_structure(self.test_project.name)
#        self.clean_database()
        cfg.CURRENT_DIR = self.old_config_file
        
        
    def test_portlet_configurable_interface(self):
        """
        A simple test for the get configurable interface method.
        """        
        test_portlet = dao.get_portlet_by_identifier("TA1TA2")
        
        result = PortletConfigurer(test_portlet).get_configurable_interface()
        self.assertEqual(len(result), 2, "Length of the resulting interface not as expected")
        for one_entry in result:
            for entry in one_entry.interface:
                if entry['name'] == 'test1':
                    self.assertTrue(entry['default'] == 'step_0[0]', "Overwritten default not in effect.")
                if entry['name'] == 'test2':
                    self.assertTrue(entry['default'] == '0', "Value that was not overwritten changed.")
        
        
def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(PythonPortletsTest))
    return test_suite


if __name__ == "__main__":
    #So you can run tests from this package individually.
    unittest.main() 
    
    
