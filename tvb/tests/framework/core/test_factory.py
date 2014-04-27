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

 A Factory class to be used in tests for generating default entities:
Project, User, Operation, basic imports (e.g. CFF).

.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>

"""

import os
import json
import random
import demo_data.cff as cff_dataset
from hashlib import md5
import tvb.config as config
from tvb.core.entities import model
from tvb.core.entities.storage import dao
from tvb.core.entities.model import BurstConfiguration
from tvb.core.entities.transient.burst_configuration_entities import WorkflowStepConfiguration as wf_cfg
from tvb.core.entities.transient.structure_entities import DataTypeMetaData
from tvb.core.services.project_service import ProjectService
from tvb.core.services.flow_service import FlowService
from tvb.core.services.operation_service import OperationService
from tvb.core.adapters.abcadapter import ABCAdapter


class TestFactory():
    """
    Expose mostly static methods for creating different entities used in tests.
    """
    @staticmethod
    def get_entity(project, expected_data, filters=None):
        """
        Return the first entity with class given by `expected_data`

        :param expected_data: specifies the class whose entity is returned
        """
        data_types = FlowService().get_available_datatypes(project.id,
                                                           expected_data.module + "." + expected_data.type, filters)
        entity = ABCAdapter.load_entity_by_gid(data_types[0][2])
        return entity
    
    @staticmethod
    def get_entity_count(project, datatype):
        """
        Return the count of stored datatypes with class given by `datatype`

        :param datatype: the class whose entities are counted
        """
        data_types = FlowService().get_available_datatypes(project.id, datatype.module + "." + datatype.type)
        return len(data_types)
    
    @staticmethod
    def create_user(username='test_user', password='test_pass',
                    mail='test_mail@tvb.org', validated=True, role='test'):
        """
        Create persisted User entity.
        
        :returns: User entity after persistence.
        """
        user = model.User(username, password, mail, validated, role)
        return dao.store_entity(user) 
    
    
    @staticmethod
    def create_project(admin, name="TestProject", description='description', users=None):
        """
        Create persisted Project entity, with no linked DataTypes.
        
        :returns: Project entity after persistence.
        """
        if users is None:
            users = []
        data = dict(name=name, description=description, users=users)
        return ProjectService().store_project(admin, True, None, **data)
    
    
    @staticmethod
    def create_figure(operation_id, user_id, project_id, session_name=None, 
                      name=None, path=None, file_format='PNG'):
        """
        :returns: the `model.ResultFigure` for a result with the given specifications
        """
        figure = model.ResultFigure(operation_id, user_id, project_id, 
                                    session_name, name, path, file_format)
        return dao.store_entity(figure)
    
    
    @staticmethod
    def create_operation(algorithm=None, test_user=None, test_project=None, 
                         operation_status=model.STATUS_FINISHED, parameters="test params"):
        """
        Create persisted operation.
        
        :param algorithm: When not None, introspect TVB and TVB_TEST for adapters.
        :return: Operation entity after persistence. 
        """
        if algorithm is None:
            algo_group = dao.find_group('tvb.tests.framework.adapters.ndimensionarrayadapter', 'NDimensionArrayAdapter')
            algorithm = dao.get_algorithm_by_group(algo_group.id)
            
        if test_user is None:
            test_user = TestFactory.create_user()
            
        if test_project is None:
            test_project = TestFactory.create_project(test_user)
            
        meta = {DataTypeMetaData.KEY_SUBJECT: "John Doe",
                DataTypeMetaData.KEY_STATE: "RAW_DATA"}
        operation = model.Operation(test_user.id, test_project.id, algorithm.id, parameters, meta=json.dumps(meta),
                                    status=operation_status, method_name=ABCAdapter.LAUNCH_METHOD)
        dao.store_entity(operation)
        ### Make sure lazy attributes are correctly loaded.
        return dao.get_operation_by_id(operation.id)
    
    
    @staticmethod
    def create_group(test_user=None, test_project=None, subject="John Doe"):
        """
        Create a group of 2 operations, each with at least one resultant DataType.
        """
        if test_user is None:
            test_user = TestFactory.create_user()  
        if test_project is None:
            test_project = TestFactory.create_project(test_user)
           
        ### Retrieve Adapter instance 
        algo_group = dao.find_group('tvb.tests.framework.adapters.testadapter3', 'TestAdapter3')
        algo_category = dao.get_category_by_id(algo_group.fk_category)
        algo = dao.get_algorithm_by_group(algo_group.id) 
        
        adapter_inst = TestFactory.create_adapter(algo_group=algo_group, test_project=test_project)
        adapter_inst.meta_data = {DataTypeMetaData.KEY_SUBJECT: subject}
        args = {model.RANGE_PARAMETER_1: 'param_5', 'param_5': [1, 2]}
        
        ### Prepare Operations group. Execute them synchronously
        service = OperationService()
        operations = service.prepare_operations(test_user.id, test_project.id, algo, algo_category, {}, **args)[0]
        service.launch_operation(operations[0].id, False, adapter_inst)
        service.launch_operation(operations[1].id, False, adapter_inst)
        
        resulted_dts = dao.get_datatype_in_group(operations[0].fk_operation_group)
        return resulted_dts, operations[0].fk_operation_group
        
    
    @staticmethod
    def create_adapter(algo_group=None, test_project=None, ):
        """
        :returns: Adapter Class after initialization.
        """
        if algo_group is None:
            algo_group = dao.find_group('tvb.tests.framework.adapters.ndimensionarrayadapter', 'NDimensionArrayAdapter')
            
        if test_project is None:
            test_user = TestFactory.create_user()
            test_project = TestFactory.create_project(test_user)
            
        group, _ = FlowService().prepare_adapter(test_project.id, algo_group)
        return FlowService().build_adapter_instance(group)
    
    
    @staticmethod
    def store_burst(project_id, simulator_config=None):
        """
        Build and persist BurstConfiguration entity.
        """
        burst = BurstConfiguration(project_id)
        if simulator_config is not None:
            burst.simulator_configuration = simulator_config
        burst.prepare_before_save()
        return dao.store_entity(burst)    
    
    
    @staticmethod
    def create_workflow_step(module, classname, static_kwargs=None, dynamic_kwargs=None,
                             step_index=0, base_step=0, tab_index=0, index_in_tab=0, is_view_step=False):
        """
        Build non-persisted WorkflowStep entity.
        """
        if static_kwargs is None:
            static_kwargs = {}
        if dynamic_kwargs is None:
            dynamic_kwargs = {}
        step_group = dao.find_group(module, classname)
        algorithm = dao.get_algorithm_by_group(step_group.id)
        second_step_configuration = wf_cfg(algorithm.id, static_kwargs, dynamic_kwargs)
        
        static_params = second_step_configuration.static_params
        dynamic_params = second_step_configuration.dynamic_params
        for entry in dynamic_params:
            dynamic_params[entry][wf_cfg.STEP_INDEX_KEY] += base_step
         
        if is_view_step:
            return model.WorkflowStepView(algorithm_id=algorithm.id, tab_index=tab_index, index_in_tab=index_in_tab,
                                          static_param=static_params, dynamic_param=dynamic_params)
        return model.WorkflowStep(algorithm_id=algorithm.id, step_index=step_index, tab_index=tab_index,
                                  index_in_tab=index_in_tab, static_param=static_params, dynamic_param=dynamic_params)
    
                 
    @staticmethod
    def import_cff(cff_path=None, test_user=None, test_project=None):
        """
        This method is used for importing a CFF data-set (load CFF_Importer, launch it).
        :param cff_path: absolute path where CFF file exists. When None, a default CFF will be used.
        :param test_user: optional persisted User instance, to use as Operation->launcher
        :param test_project: optional persisted Project instance, to use for launching Operation in it. 
        """
        ### Prepare Data
        if cff_path is None:
            cff_path = os.path.join(os.path.dirname(cff_dataset.__file__), 'dataset_74.cff')
        if test_user is None:
            test_user = TestFactory.create_user()  
        if test_project is None:
            test_project = TestFactory.create_project(test_user)  
            
        ### Retrieve Adapter instance 
        group = dao.find_group('tvb.adapters.uploaders.cff_importer', 'CFF_Importer')
        importer = ABCAdapter.build_adapter(group)
        args = {'cff': cff_path, DataTypeMetaData.KEY_SUBJECT: DataTypeMetaData.DEFAULT_SUBJECT}
        
        ### Launch Operation
        FlowService().fire_operation(importer, test_user, test_project.id, **args)
        
        
    @staticmethod
    def import_surface_zip(user, project, zip_path, surface_type, zero_based):
        ### Retrieve Adapter instance 
        group = dao.find_group('tvb.adapters.uploaders.zip_surface_importer', 'ZIPSurfaceImporter')
        importer = ABCAdapter.build_adapter(group)
        args = {'uploaded': zip_path, 'surface_type': surface_type,
                'zero_based_triangles': zero_based}
        
        ### Launch Operation
        FlowService().fire_operation(importer, user, project.id, **args)
        
        
    @staticmethod
    def import_sensors(user, project, zip_path, sensors_type):
        ### Retrieve Adapter instance 
        group = dao.find_group('tvb.adapters.uploaders.sensors_importer', 'Sensors_Importer')
        importer = ABCAdapter.build_adapter(group)
        args = {'sensors_file': zip_path, 'sensors_type': sensors_type}
        ### Launch Operation
        FlowService().fire_operation(importer, user, project.id, **args)
    
    
    @staticmethod
    def import_zip_connectivity(user, project, subject, zip_path):
        group = dao.find_group('tvb.adapters.uploaders.zip_connectivity_importer', 'ZIPConnectivityImporter')
        importer = ABCAdapter.build_adapter(group)
        FlowService().fire_operation(importer, user, project.id, uploaded=zip_path, Data_Subject=subject)


class ExtremeTestFactory():
    """
    Test Factory for random and large number of users.
    """
    
    VALIDATION_DICT = {}

    @staticmethod
    def get_users_ids(wanted_nr, total_nr, exclude_id, available_users):
        """
        Generate random users
        """
        nr_users = 0
        result = []
        while nr_users < wanted_nr:
            new_idx = random.randint(0, total_nr - 1)
            new_id = available_users[new_idx].id
            if new_id not in result and new_id != exclude_id:
                ExtremeTestFactory.VALIDATION_DICT[new_id] += 1
                result.append(new_id)
                nr_users += 1
        return result
    
    
    @staticmethod
    def generate_users(nr_users, nr_projects):
        """
        The generate_users method will create a clean state db with
        :param nr_users: number of users to be generated (with random roles between
                                CLINICIAN and RESEARCHER and random validated state)
        :param nr_projects: maximum number of projects to be generated for each user
        """
        config.EVENTS_FOLDER = ''
        users = []
        
        for i in range(nr_users):
            coin_flip = random.randint(0, 1)
            role = 'CLINICIAN' if coin_flip == 1 else 'RESEARCHER'
            password = md5("test").hexdigest()
            new_user = model.User("gen" + str(i), password, "test_mail@tvb.org", True, role)
            dao.store_entity(new_user)
            new_user = dao.get_user_by_name("gen" + str(i))
            ExtremeTestFactory.VALIDATION_DICT[new_user.id] = 0
            users.append(new_user)
            
        for i in range(nr_users):
            current_user = dao.get_user_by_name("gen" + str(i))
            projects_for_user = random.randint(0, nr_projects)
            for j in range(projects_for_user):         
                data = dict(name='GeneratedProject' + str(i) + '_' + str(j),
                            description='test_desc',
                            users=ExtremeTestFactory.get_users_ids(random.randint(0, nr_users - 3),
                                                                   nr_users, current_user.id, users))
                ProjectService().store_project(current_user, True, None, **data)
                ExtremeTestFactory.VALIDATION_DICT[current_user.id] += 1 
                
                   
    