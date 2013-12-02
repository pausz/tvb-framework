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
.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
.. moduleauthor:: Ionel Ortelecan <ionel.ortelecan@codemart.ro>
"""
import os
import shutil
import unittest
import numpy
from tvb.basic.config.settings import TVBSettings as cfg
from tvb.core.entities.storage import dao
from tvb.core.entities.file.files_helper import FilesHelper
from tvb.core.services.import_service import ImportService
from tvb.core.services.flow_service import FlowService
from tvb.core.services.project_service import ProjectService
from tvb.core.services.operation_service import OperationService
from tvb.core.services.exceptions import ProjectImportException
from tvb.core.adapters.abcadapter import ABCAdapter
from tvb.adapters.exporters.export_manager import ExportManager
from tvb.datatypes.mapped_values import ValueWrapper
from tvb.datatypes.time_series import TimeSeries
from tvb.tests.framework.core.test_factory import TestFactory
from tvb.tests.framework.adapters.storeadapter import StoreAdapter
from tvb.tests.framework.core.base_testcase import TransactionalTestCase



class ImportServiceTest(TransactionalTestCase):
    """
    This class contains tests for the tvb.core.services.import_service module.
    """  
    
    def setUp(self):
        """
        Reset the database before each test.
        """
        self.import_service = ImportService()
        self.flow_service = FlowService()
        self.project_service = ProjectService()
        
        self.test_user = TestFactory.create_user()
        self.test_project = TestFactory.create_project(self.test_user, name="GeneratedProject", description="test_desc")
        self.operation = TestFactory.create_operation(test_user=self.test_user, test_project=self.test_project)
        self.adapter_instance = TestFactory.create_adapter(test_project=self.test_project)
        TestFactory.import_cff(test_user=self.test_user, test_project=self.test_project)
        self.zip_path = None 
        

    def tearDown(self):
        """
        Reset the database when test is done.
        """
        ### Delete TEMP folder
        if os.path.exists(cfg.TVB_TEMP_FOLDER):
            shutil.rmtree(cfg.TVB_TEMP_FOLDER)
        
        ### Delete folder where data was exported
        if os.path.exists(self.zip_path):
            shutil.rmtree(os.path.split(self.zip_path)[0])
            
        self.delete_project_folders()

            
    def test_import_export(self):
        """
        Test the import/export mechanism for a project structure.
        The project contains the following data types: Connectivity, Surface, MappedArray and ValueWrapper.
        """
        result = self.get_all_datatypes()
        expected_results = {}
        for one_data in result:
            expected_results[one_data.gid] = (one_data.module, one_data.type)
        
        #create an array mapped in DB
        data = {'param_1': 'some value'}
        OperationService().initiate_prelaunch(self.operation, self.adapter_instance, {}, **data)
        inserted = self.flow_service.get_available_datatypes(self.test_project.id, "tvb.datatypes.arrays.MappedArray")
        self.assertEqual(len(inserted), 2, "Problems when inserting data")
        
        #create a value wrapper
        value_wrapper = self._create_value_wrapper()
        result = dao.get_filtered_operations(self.test_project.id, None)
        self.assertEqual(len(result), 2, "Should be two operations before export and not " + str(len(result)) + " !")
        self.zip_path = ExportManager().export_project(self.test_project)
        self.assertTrue(self.zip_path is not None, "Exported file is none")
        
        # Now remove the original project
        self.project_service.remove_project(self.test_project.id)
        result, lng_ = self.project_service.retrieve_projects_for_user(self.test_user.id)
        self.assertEqual(0, len(result), "Project Not removed!")
        self.assertEqual(0, lng_, "Project Not removed!")
        
        # Now try to import again project
        self.import_service.import_project_structure(self.zip_path, self.test_user.id)
        result = self.project_service.retrieve_projects_for_user(self.test_user.id)[0]
        self.assertEqual(len(result), 1, "There should be only one project.")
        self.assertEqual(result[0].name, "GeneratedProject", "The project name is not correct.")
        self.assertEqual(result[0].description, "test_desc", "The project description is not correct.")
        self.test_project = result[0]
        
        result = dao.get_filtered_operations(self.test_project.id, None)
        
        #1 op. - import project; 1 op. - save the array wrapper
        self.assertEqual(len(result), 2, "Should be two operations after export and not " + str(len(result)) + " !")
        for gid in expected_results:
            datatype = dao.get_datatype_by_gid(gid)
            self.assertEqual(datatype.module, expected_results[gid][0], 'DataTypes not imported correctly')
            self.assertEqual(datatype.type, expected_results[gid][1], 'DataTypes not imported correctly')
        #check the value wrapper
        new_val = self.flow_service.get_available_datatypes(self.test_project.id, 
                                                            "tvb.datatypes.mapped_values.ValueWrapper")
        self.assertEqual(len(new_val), 1, "One !=" + str(len(new_val)))
        new_val = ABCAdapter.load_entity_by_gid(new_val[0][2])
        self.assertEqual(value_wrapper.data_value, new_val.data_value, "Data value incorrect")
        self.assertEqual(value_wrapper.data_type, new_val.data_type, "Data type incorrect")
        self.assertEqual(value_wrapper.data_name, new_val.data_name, "Data name incorrect")
        

    def test_import_export_existing(self):
        """
        Test the import/export mechanism for a project structure.
        The project contains the following data types: Connectivity, Surface, MappedArray and ValueWrapper.
        """
        result = self.get_all_datatypes()
        expected_results = {}
        for one_data in result:
            expected_results[one_data.gid] = (one_data.module, one_data.type)
        
        #create an array mapped in DB
        data = {'param_1': 'some value'}
        OperationService().initiate_prelaunch(self.operation, self.adapter_instance, {}, **data)
        inserted = self.flow_service.get_available_datatypes(self.test_project.id, "tvb.datatypes.arrays.MappedArray")
        self.assertEqual(len(inserted), 2, "Problems when inserting data")
        
        #create a value wrapper
        self._create_value_wrapper()
        result = dao.get_filtered_operations(self.test_project.id, None)
        self.assertEqual(len(result), 2, "Should be two operations before export and not " + str(len(result)) + " !")
        self.zip_path = ExportManager().export_project(self.test_project)
        self.assertTrue(self.zip_path is not None, "Exported file is none")
        
        try:
            self.import_service.import_project_structure(self.zip_path, self.test_user.id)
            self.fail("Invalid import as the project already exists!")
        except ProjectImportException:
            #OK, do nothing. The project already exists.
            pass


    def _create_timeseries(self):
        """Launch adapter to persist a TimeSeries entity"""
        activity_data = numpy.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])
        time_data = numpy.array([1, 2, 3])
        storage_path = FilesHelper().get_project_folder(self.test_project)
        time_series = TimeSeries(time_files=None, activity_files=None, 
                                 max_chunk=10, maxes=None, mins=None, data_shape=numpy.shape(activity_data), 
                                 storage_path=storage_path, label_y="Time", time_data=time_data, data_name='TestSeries',
                                 activity_data=activity_data, sample_period=10.0)
        self._store_entity(time_series, "TimeSeries", "tvb.datatypes.time_series")
        timeseries = self.flow_service.get_available_datatypes(self.test_project.id, 
                                                               "tvb.datatypes.time_series.TimeSeries")
        self.assertEqual(len(timeseries), 1, "Should be only one TimeSeries")


    def _create_value_wrapper(self):
        """Persist ValueWrapper"""
        value_ = ValueWrapper(data_value=5.0, data_name="my_value")
        self._store_entity(value_, "ValueWrapper", "tvb.datatypes.mapped_values")
        valuew = self.flow_service.get_available_datatypes(self.test_project.id,
                                                           "tvb.datatypes.mapped_values.ValueWrapper")
        self.assertEqual(len(valuew), 1, "Should be only one value wrapper")
        return ABCAdapter.load_entity_by_gid(valuew[0][2])


    def _store_entity(self, entity, type_, module):
        """Launch adapter to store a create a persistent DataType."""
        entity.type = type_
        entity.module = module
        entity.subject = "John Doe"
        entity.state = "RAW_STATE"
        entity.set_operation_id(self.operation.id)
        adapter_instance = StoreAdapter([entity])
        OperationService().initiate_prelaunch(self.operation, adapter_instance, {})

    
def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(ImportServiceTest))
    return test_suite


if __name__ == "__main__":
    #So you can run tests from this package individually.
    TEST_RUNNER = unittest.TextTestRunner()
    TEST_SUITE = suite()
    TEST_RUNNER.run(TEST_SUITE)




