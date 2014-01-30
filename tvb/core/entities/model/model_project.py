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
Here we define entities related to user and project.

.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
.. moduleauthor:: Yann Gordon <yann@tvb.invalid>
"""

import datetime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy import Boolean, Integer, String, DateTime, Column, ForeignKey, Float
from tvb.core import utils
from tvb.core.entities.exportable import Exportable
from tvb.core.entities.model.model_base import Base
from tvb.basic.logger.builder import get_logger
from tvb.basic.config.settings import TVBSettings

LOG = get_logger(__name__)


#Constants for User Roles.
ROLE_ADMINISTRATOR = "ADMINISTRATOR"
ROLE_CLINICIAN = "CLINICIAN"
ROLE_RESEARCHER = "RESEARCHER"

USER_ROLES = [ROLE_ADMINISTRATOR, ROLE_CLINICIAN, ROLE_RESEARCHER]



class User(Base):
    """
    Contains the users informations.
    """
    __tablename__ = 'USERS'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    email = Column(String, nullable=True)
    role = Column(String)
    validated = Column(Boolean)
    selected_project = Column(Integer)
    used_disk_space = Column(Float)

    preferences = association_proxy('user_preferences', 'value',
                                    creator=lambda k, v: UserPreferences(key=k, value=v))


    def __init__(self, login, password, email=None, validated=True, role=ROLE_RESEARCHER, used_disk_space=0):
        self.username = login
        self.password = password
        self.email = email
        self.validated = validated
        self.role = role
        self.used_disk_space = used_disk_space


    def __repr__(self):
        return "<USER('%s','%s','%s','%s','%s', %s)>" % (self.username, self.password, self.email, self.validated,
                                                         self.role, str(self.selected_project))


    def is_administrator(self):
        """Return a boolean, saying if current user has role Administrator"""
        return self.role == ROLE_ADMINISTRATOR


    def is_online_help_active(self):
        """
        This method returns True if this user should see online help.
        """
        is_help_active = True
        if UserPreferences.ONLINE_HELP_ACTIVE in self.preferences:
            flag_str = self.preferences[UserPreferences.ONLINE_HELP_ACTIVE]
            is_help_active = utils.string2bool(flag_str)

        return is_help_active


    def switch_online_help_state(self):
        """
        This method changes the state of the OnlineHelp Active flag.
        """
        new_state = utils.bool2string(not self.is_online_help_active())
        self.preferences[UserPreferences.ONLINE_HELP_ACTIVE] = new_state



class UserPreferences(Base):
    """
    Contains the user preferences data.
    """
    __tablename__ = 'USER_PREFERENCES'

    ONLINE_HELP_ACTIVE = "online_help_active"

    fk_user = Column(Integer, ForeignKey('USERS.id'), primary_key=True)
    key = Column(String, primary_key=True)
    value = Column(String)

    user = relationship(User, backref=backref("user_preferences", cascade="all, delete-orphan", lazy='joined',
                                              collection_class=attribute_mapped_collection("key")))


    def __repr__(self):
        return 'UserPreferences: %s - %s' % (self.key, self.value)



class Project(Base, Exportable):
    """
    Contains the Projects informations and who is the administrator.
    """
    __tablename__ = 'PROJECTS'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    last_updated = Column(DateTime)
    fk_admin = Column(Integer, ForeignKey('USERS.id'))
    gid = Column(String, unique=True)

    administrator = relationship(User, backref=backref('PROJECTS', order_by=id))

    ### Transient Attributes
    operations_finished = 0
    operations_started = 0
    operations_error = 0
    members = []

    def __init__(self, name, fk_admin, description=''):
        self.name = name
        self.fk_admin = fk_admin
        self.description = description
        self.gid = utils.generate_guid()
        self.version = TVBSettings.PROJECT_VERSION


    def refresh_update_date(self):
        """Mark entity as being changed NOW. (last_update field)"""
        self.last_updated = datetime.datetime.now()


    def __repr__(self):
        return "<Project('%s', '%s')>" % (self.name, self.fk_admin)


    def to_dict(self):
        """
        Overwrite superclass method to add required changes.
        """
        _, base_dict = super(Project, self).to_dict(excludes=['id', 'fk_admin', 'administrator', 'trait'])
        return self.__class__.__name__, base_dict


    def from_dict(self, dictionary, user_id):
        """
        Add specific attributes from a input dictionary.
        """
        self.name = dictionary['name']
        self.description = dictionary['description']
        self.last_updated = datetime.datetime.now()
        self.gid = dictionary['gid']
        self.fk_admin = user_id
        return self



class User_to_Project(Base):
    """
    Multiple Users can be members of a given Project.
    """
    __tablename__ = 'USERS_TO_PROJECTS'

    id = Column(Integer, primary_key=True)
    fk_user = Column(Integer, ForeignKey('USERS.id', ondelete="CASCADE"))
    fk_project = Column(Integer, ForeignKey('PROJECTS.id', ondelete="CASCADE"))


    def __init__(self, user, case):

        if type(user) == int:
            self.fk_user = user
        else:
            self.fk_user = user.id

        if type(case) == int:
            self.fk_project = case
        else:
            self.fk_project = case.id   
    
            
