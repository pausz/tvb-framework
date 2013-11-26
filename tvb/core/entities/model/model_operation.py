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
Here we define entities for Operations and Algorithms.

.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
.. moduleauthor:: Yann Gordon <yann@tvb.invalid>
"""

import json
import datetime
from tvb.basic.logger.builder import get_logger
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Boolean, Integer, String, DateTime, Column, ForeignKey

from tvb.config import TVB_IMPORTER_CLASS, TVB_IMPORTER_MODULE
from tvb.core.utils import string2date, generate_guid
from tvb.core.entities.exportable import Exportable
from tvb.core.entities.model.model_base import Base
from tvb.core.entities.model.model_project import Project, User
from tvb.core.utils import string2bool, date2string, LESS_COMPLEX_TIME_FORMAT


LOG = get_logger(__name__)



class AlgorithmCategory(Base):
    """
    A category that will have different boolean attributes 
    e.g.: launchable|rawinput|
    display, a displayName and a default state for data.
    """
    __tablename__ = 'ALGORITHM_CATEGORIES'

    id = Column(Integer, primary_key=True)
    displayname = Column(String)
    launchable = Column(Boolean)
    rawinput = Column(Boolean)
    display = Column(Boolean)
    defaultdatastate = Column(String)
    order_nr = Column(Integer)
    last_introspection_check = Column(DateTime)


    def __init__(self, displayname, launchable=False, rawinput=False,
                 display=False, defaultdatastate='', order_nr='999',
                 last_introspection_check=None):
        self.displayname = displayname
        self.launchable = launchable
        self.rawinput = rawinput
        self.display = display
        self.defaultdatastate = defaultdatastate
        self.order_nr = order_nr
        self.last_introspection_check = last_introspection_check


    def __repr__(self):
        return "<AlgorithmCategory('%s', '%s', '%s', '%s', '%s')>" % (self.displayname, self.launchable,
                                                                      self.rawinput, self.display,
                                                                      self.defaultdatastate)


    def __hash__(self):
        return hash((self.displayname, self.launchable, self.rawinput,
                     self.display, self.defaultdatastate, self.order_nr))


    def __eq__(self, other):
        return (isinstance(other, AlgorithmCategory) and
                self.displayname == other.displayname and
                self.launchable == other.launchable
                and self.rawinput == other.rawinput
                and self.display == other.display
                and self.defaultdatastate == other.defaultdatastate)



class AlgorithmGroup(Base):
    """
    Group = Simulation|Analysis|Visualization|Upload adapter group reference.
    Store module, className - to rebuild a Python import string dynamically.
    Store algorithm_param_name and - to launch an algorithm automatically. 
    """
    __tablename__ = 'ALGORITHM_GROUPS'

    id = Column(Integer, primary_key=True)
    module = Column(String)
    classname = Column(String)
    fk_category = Column(Integer, ForeignKey('ALGORITHM_CATEGORIES.id', ondelete="CASCADE"))
    algorithm_param_name = Column(String)
    displayname = Column(String)
    description = Column(String)
    subsection_name = Column(String)
    ui_display = Column(Integer)        # When negative the algorithm will not be displayed on the STEPS page.
    init_parameter = Column(String)
    last_introspection_check = Column(DateTime)

    group_category = relationship(AlgorithmCategory, backref=backref('ALGORITHM_GROUPS',
                                                                     order_by=id, cascade="delete, all"))
    algorithms = relationship('Algorithm', cascade="delete, all")


    def __init__(self, module, classname, category_key, algorithm_param_name=None, init_parameter=None,
                 last_introspection_check=None, description=None, subsection_name=None):
        self.module = module
        self.classname = classname
        self.fk_category = category_key
        self.algorithm_param_name = algorithm_param_name
        self.init_parameter = init_parameter
        self.last_introspection_check = last_introspection_check
        if description is None:
            self.description = ""
        else:
            self.description = description
        if subsection_name is not None:
            self.subsection_name = subsection_name
        else:
            self.subsection_name = self.module.split('.')[-1].replace('_adapter', '')


    def __repr__(self):
        return "<Group('%s', '%s', '%s', '%s', '%s', '%s')>" % (self.classname,
                                                                self.module, self.fk_category, self.displayname,
                                                                self.algorithm_param_name, self.init_parameter)



class Algorithm(Base):
    """
    An algorithm will be part of a group. The module and ClassName are those of it's corresponding
    group. It will thus have a groupId, an Identifier(none if single algorithm in module or unique
    per algorithm is more than one algorithm launched from same group) additionally it will hold
    the required DataType input, the input parameter name and the outputList.
    """
    __tablename__ = 'ALGORITHMS'

    id = Column(Integer, primary_key=True)
    fk_algo_group = Column(Integer, ForeignKey('ALGORITHM_GROUPS.id', ondelete="CASCADE"))
    identifier = Column(String)
    name = Column(String)
    required_datatype = Column(String)
    datatype_filter = Column(String)
    parameter_name = Column(String)
    outputlist = Column(String)
    description = Column(String)

    algo_group = relationship(AlgorithmGroup, backref=backref('ALGORITHMS', order_by=id, cascade="delete, all"))


    def __init__(self, group_id, identifier, name='', req_data='', param_name='',
                 output='', datatype_filter='', description=''):
        self.fk_algo_group = group_id
        self.identifier = identifier
        self.required_datatype = req_data
        self.parameter_name = param_name
        self.outputlist = output
        self.name = name
        self.datatype_filter = datatype_filter
        self.description = description


    def __repr__(self):
        return "<Group('%d', '%s', '%s', %s', '%s', '%s')>" % (self.fk_algo_group, self.identifier, self.name,
                                                               self.required_datatype, self.parameter_name,
                                                               self.outputlist)


RANGE_MISSING_STRING = "-"


class OperationGroup(Base, Exportable):
    """
    We use this group entity, to map in DB a group of operations started 
    in the same time by the user
    """
    __tablename__ = "OPERATION_GROUPS"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    range1 = Column(String)
    range2 = Column(String)
    range3 = Column(String)
    gid = Column(String)
    fk_launched_in = Column(Integer, ForeignKey('PROJECTS.id', ondelete="CASCADE"))
    project = relationship(Project, backref=backref('OPERATION_GROUPS', order_by=id, cascade="all,delete"))


    def __init__(self, project_id, name='incomplete', ranges=None):
        self.name = name
        if ranges:
            if len(ranges) > 0:
                self.range1 = ranges[0]
            if len(ranges) > 1:
                self.range2 = ranges[1]
            if len(ranges) > 2:
                self.range3 = ranges[2]
        self.gid = generate_guid()
        self.fk_launched_in = project_id


    def __repr__(self):
        return "<OperationGroup(%s,%s)>" % (self.name, self.gid)


    @property
    def range_references(self):
        """Memorized range starter"""
        ranges = [self.range1]
        if self.range2 and self.range2 != 'null':
            ranges.append(self.range2)
        if self.range3 and self.range3 != 'null':
            ranges.append(self.range3)
        return ranges


    def fill_operationgroup_name(self, entities_in_group):
        """
        Display name for UI.
        """
        new_name = "of " + entities_in_group + " varying "
        if self.range1 is not None:
            new_name += json.loads(self.range1)[0]
        if self.range2 is not None:
            new_name += " x " + json.loads(self.range2)[0]
        if self.range3 is not None:
            new_name += " x " + json.loads(self.range3)[0]

        new_name += " - " + date2string(datetime.datetime.now(), date_format=LESS_COMPLEX_TIME_FORMAT)
        self.name = new_name


    @staticmethod
    def load_range_numbers(range_value):
        """
        Parse the range values for a given json-like string.

        :returns: Boolean_are_all_numbers, range_field_name, array_range_values)
        """
        if range_value is None:
            return None, RANGE_MISSING_STRING, [RANGE_MISSING_STRING]

        loaded_json = json.loads(range_value)
        range_name = loaded_json[0]
        range_values = loaded_json[1]
        can_interpolate_range = True  # Assume this is a numeric range that we can interpolate
        for idx, entry in enumerate(range_values):
            try:
                range_values[idx] = float(entry)
            except ValueError:
                # It's a DataType range
                can_interpolate_range = False
        return can_interpolate_range, range_name, range_values


    @property
    def has_only_numeric_ranges(self):
        """
        :returns: True when all range fields are either None or could be parsed into a numeric array.
        """
        is_numeric = [self.load_range_numbers(self.range1)[0],
                      self.load_range_numbers(self.range2)[0],
                      self.load_range_numbers(self.range3)[0]]

        for num in is_numeric:
            if num is False:
                return False
        return True



#Possible values for Operation.status field
STATUS_STARTED = "3-STARTED"
STATUS_FINISHED = "4-FINISHED"
STATUS_CANCELED = "2-CANCELED"
STATUS_ERROR = "1-ERROR"



class Operation(Base, Exportable):
    """
    The class used to log any action executed in Projects.
    """
    __tablename__ = 'OPERATIONS'

    id = Column(Integer, primary_key=True)
    fk_launched_by = Column(Integer, ForeignKey('USERS.id'))
    fk_launched_in = Column(Integer, ForeignKey('PROJECTS.id', ondelete="CASCADE"))
    fk_from_algo = Column(Integer, ForeignKey('ALGORITHMS.id'))
    fk_operation_group = Column(Integer, ForeignKey('OPERATION_GROUPS.id', ondelete="CASCADE"), default=None)
    gid = Column(String)
    parameters = Column(String)
    meta_data = Column(String)
    method_name = Column(String)
    create_date = Column(DateTime)       # Date at which the user generated this entity
    start_date = Column(DateTime)        # Actual time when the operation executions is started (without queue time) 
    completion_date = Column(DateTime)   # Time when the operation got status FINISHED/ ERROR or CANCEL set.
    status = Column(String, index=True)
    visible = Column(Boolean, default=True)
    additional_info = Column(String)
    user_group = Column(String, default=None)
    range_values = Column(String, default=None)
    result_disk_size = Column(Integer)

    algorithm = relationship(Algorithm, backref=backref('OPERATIONS', order_by=id))
    project = relationship(Project, backref=backref('PROJECTS', order_by=id, cascade="all,delete"))
    operation_group = relationship(OperationGroup, backref=backref('OPERATION_GROUPS', order_by=id))
    user = relationship(User, primaryjoin=(fk_launched_by == User.id), lazy='joined')


    def __init__(self, fk_launched_by, fk_launched_in, fk_from_algo, parameters, meta='', method_name='',
                 status=STATUS_STARTED, start_date=None, completion_date=None, op_group_id=None, additional_info='',
                 user_group=None, range_values=None, result_disk_size=0):
        self.fk_launched_by = fk_launched_by
        self.fk_launched_in = fk_launched_in
        self.fk_from_algo = fk_from_algo
        self.parameters = parameters
        self.meta_data = meta
        self.method_name = method_name
        self.create_date = datetime.datetime.now()
        self.start_date = start_date
        self.completion_date = completion_date
        self.status = status
        self.fk_operation_group = op_group_id
        self.range_values = range_values
        self.user_group = user_group
        self.additional_info = additional_info
        self.gid = generate_guid()
        self.result_disk_size = result_disk_size


    def __repr__(self):
        return "<Operation(%s,%s,'%s','%s','%s','%s','%s,'%s','%s',%s, '%s')>" \
               % (self.fk_launched_by, self.fk_launched_in, self.fk_from_algo, self.parameters,
                  self.meta_data, self.status, self.method_name, self.start_date, self.completion_date,
                  self.fk_operation_group, self.user_group)


    def start_now(self):
        """ Update Operation fields at startup: Status and Date"""
        self.start_date = datetime.datetime.now()
        self.status = STATUS_STARTED


    def mark_complete(self, status, additional_info=None):
        """ Update Operation fields on completion: Status and Date"""
        self.completion_date = datetime.datetime.now()
        if additional_info is not None:
            self.additional_info = additional_info
        self.status = status


    def mark_cancelled(self):
        """Update status into CANCELED"""
        self.status = STATUS_CANCELED


    def to_dict(self):
        """
        Overwrite superclass method to add required changes.
        """
        _, base_dict = super(Operation, self).to_dict(excludes=['id', 'fk_launched_by', 'user', 'fk_launched_in',
                                                                'project', 'fk_from_algo', 'algorithm',
                                                                'fk_operation_group', 'operation_group'])
        base_dict['fk_launched_in'] = self.project.gid
        base_dict['fk_from_algo'] = json.dumps(dict(module=self.algorithm.algo_group.module,
                                                    classname=self.algorithm.algo_group.classname,
                                                    init_parameter=self.algorithm.algo_group.init_parameter,
                                                    identifier=self.algorithm.identifier))
        # We keep the information for the operation_group in this place (on each operation)
        #because we don't have an XML file for the operation_group entity.
        # We don't want to keep the information about the operation groups into the project XML file
        #because it may be opened from different places and may produce conflicts.
        if self.operation_group:
            base_dict['fk_operation_group'] = json.dumps(self.operation_group.to_dict()[1])
        return self.__class__.__name__, base_dict


    def from_dict(self, dictionary, dao, user_id=None, project_gid=None):
        """
        Add specific attributes from a input dictionary.
        """

        # If user id was specified try to load it, otherwise use System account
        user = dao.get_system_user() if user_id is None else dao.get_user_by_id(user_id)
        self.fk_launched_by = user.id

        # Find parent Project
        prj_to_load = project_gid if project_gid is not None else dictionary['fk_launched_in']
        parent_project = dao.get_project_by_gid(prj_to_load)
        self.fk_launched_in = parent_project.id
        self.project = parent_project

        # Find parent Algorithm
        source_algorithm = json.loads(dictionary['fk_from_algo'])
        init_parameter = None
        if 'init_parameter' in source_algorithm:
            init_parameter = source_algorithm['init_parameter']

        algo_group = dao.find_group(source_algorithm['module'], source_algorithm['classname'], init_parameter)

        if algo_group:
            algorithm = dao.get_algorithm_by_group(algo_group.id, source_algorithm['identifier'])
            self.algorithm = algorithm
            self.fk_from_algo = algorithm.id
        else:
            # The algorithm that produced this operation no longer exists most likely due to
            # exported operation from different version. Fallback to tvb importer.
            LOG.warning("Algorithm group %s was not found in DB. Most likely cause is that archive was exported "
                        "from a different TVB version. Using fallback TVB_Importer as source of "
                        "this operation." % (source_algorithm['module'],))
            algo_group = dao.find_group(TVB_IMPORTER_MODULE, TVB_IMPORTER_CLASS)
            algorithm = dao.get_algorithm_by_group(algo_group.id)
            self.fk_from_algo = algorithm.id
            dictionary['additional_info'] = ("The original parameters for this operation were: \nAdapter: %s "
                                             "\nParameters %s" % (source_algorithm['module'] + '.' +
                                                                  source_algorithm['classname'],
                                                                  dictionary['parameters']))

        # Find OperationGroup, if any
        if 'fk_operation_group' in dictionary:
            group_dict = json.loads(dictionary['fk_operation_group'])
            op_group = None
            if group_dict:
                op_group = dao.get_operationgroup_by_gid(group_dict['gid'])
                if not op_group:
                    name = group_dict['name']
                    ranges = [group_dict['range1'], group_dict['range2'], group_dict['range3']]
                    gid = group_dict['gid']
                    op_group = OperationGroup(self.fk_launched_in, name, ranges)
                    op_group.gid = gid
                    op_group = dao.store_entity(op_group)
            self.operation_group = op_group
            self.fk_operation_group = op_group.id
        else:
            self.operation_group = None
            self.fk_operation_group = None

        self.parameters = dictionary['parameters']
        self.meta_data = dictionary['meta_data']
        self.method_name = dictionary['method_name']
        self.create_date = string2date(dictionary['create_date'])
        if dictionary['start_date'] != "None":
            self.start_date = string2date(dictionary['start_date'])
        if dictionary['completion_date'] != "None":
            self.completion_date = string2date(dictionary['completion_date'])
        self.status = self._parse_status(dictionary['status'])
        self.visible = string2bool(dictionary['visible'])
        self.range_values = dictionary['range_values']
        self.user_group = dictionary['user_group']
        self.additional_info = dictionary['additional_info']
        self.gid = dictionary['gid']

        return self
    
    
    def _parse_status(self, status):
        """
        To keep backwards compatibility, when we import an operation that did not have new 
        operation status.
        """
        if status in (STATUS_FINISHED, 'FINISHED'):
            return STATUS_FINISHED
        elif status in (STATUS_ERROR, 'ERROR'):
            return STATUS_ERROR
        elif status in (STATUS_CANCELED, 'CANCELED'):
            return STATUS_CANCELED
        return STATUS_STARTED



class OperationProcessIdentifier(Base):
    """
    Class for storing for each operation the process identifier under which
    it was launched so any operation can be stopped from tvb.
    """
    __tablename__ = "OPERATION_PROCESS_IDENTIFIERS"

    id = Column(Integer, primary_key=True)
    fk_from_operation = Column(Integer, ForeignKey('OPERATIONS.id', ondelete="CASCADE"))
    pid = Column(String)
    job_id = Column(String)

    operation = relationship(Operation, backref=backref('OPERATION_PROCESS_IDENTIFIERS', order_by=id, cascade="delete"))


    def __init__(self, operation_id, pid=None, job_id=None):
        self.fk_from_operation = operation_id
        self.pid = pid
        self.job_id = job_id



class ResultFigure(Base, Exportable):
    """
    Class for storing figures from results, visualize them eventually next to each other.
    A group of results, with the same session_name will be displayed 
    """
    __tablename__ = 'RESULT_FIGURES'

    id = Column(Integer, primary_key=True)
    fk_from_operation = Column(Integer, ForeignKey('OPERATIONS.id', ondelete="CASCADE"))
    fk_for_user = Column(Integer, ForeignKey('USERS.id', ondelete="CASCADE"))
    fk_in_project = Column(Integer, ForeignKey('PROJECTS.id', ondelete="CASCADE"))
    project = relationship(Project, backref=backref('RESULT_FIGURES', order_by=id, cascade="delete"))
    operation = relationship(Operation, backref=backref('RESULT_FIGURES', order_by=id, cascade="delete"))
    session_name = Column(String)
    name = Column(String)
    file_path = Column(String)
    file_format = Column(String)


    def __init__(self, operation_id, user_id, project_id, session_name, name, path, file_format="PNG"):
        self.fk_from_operation = operation_id
        self.fk_for_user = user_id
        self.fk_in_project = project_id
        self.session_name = session_name
        self.name = name
        self.file_path = path
        self.file_format = file_format.lower()          # some platforms have difficulties if it's not lower case


    def __repr__(self):
        return "<ResultFigure(%d, %d, %d, %s, %s, %s, %s)>" % (self.fk_from_operation, self.fk_for_user,
                                                               self.fk_in_project, self.session_name, self.name,
                                                               self.file_path, self.file_format)


    def to_dict(self):
        """
        Overwrite superclass method with required additional data.
        """
        _, base_dict = super(ResultFigure, self).to_dict(excludes=['id', 'fk_from_operation', 'fk_for_user',
                                                                   'fk_in_project', 'operation', 'project'])
        base_dict['fk_from_operation'] = self.operation.gid
        base_dict['fk_in_project'] = self.project.gid
        return self.__class__.__name__, base_dict


    def from_dict(self, dictionary):
        """
        Add specific attributes from a input dictionary.
        """
        self.fk_from_operation = dictionary['fk_op_id']
        self.fk_for_user = dictionary['fk_user_id']
        self.fk_in_project = dictionary['fk_project_id']
        self.session_name = dictionary['session_name']
        self.name = dictionary['name']
        self.file_path = dictionary['file_path']
        self.file_format = dictionary['file_format']
        return self
    
    
    
    