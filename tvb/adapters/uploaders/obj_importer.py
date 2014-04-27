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
.. moduleauthor:: Mihai Andrei <mihai.andrei@codemart.ro>
"""

from tvb.adapters.uploaders.abcuploader import ABCUploader
from tvb.adapters.uploaders.constants import OPTION_SURFACE_CORTEX, OPTION_SURFACE_SKINAIR, OPTION_SURFACE_FACE
from tvb.adapters.uploaders.handler_surface import create_surface_of_type
from tvb.adapters.uploaders.obj.surface import ObjSurface
from tvb.basic.logger.builder import get_logger
from tvb.core.adapters.exceptions import ParseException, LaunchException
from tvb.core.entities.storage import transactional
from tvb.datatypes.surfaces import CorticalSurface, SkinAir, FaceSurface


class ObjSurfaceImporter(ABCUploader):
    """
    This imports geometry data stored in wavefront obj format
    """
    _ui_name = "Obj surface"
    _ui_subsection = "obj_importer"
    _ui_description = "Import geometry data stored in wavefront obj format"


    def get_upload_input_tree(self):
        """
        Take as input an obj file
        """
        return [{'name': 'surface_type', 'type': 'select',
                 'label': 'Specify file type : ', 'required': True,
                 'options': [{'name': 'Cortex', 'value': OPTION_SURFACE_CORTEX},
                             {'name': 'Outer Skin', 'value': OPTION_SURFACE_SKINAIR},
                             {'name': 'Face Shade', 'value': OPTION_SURFACE_FACE}],
                 'default': OPTION_SURFACE_FACE},

                {'name': 'data_file', 'type': 'upload', 'required_type': '.obj',
                 'label': 'Please select file to import', 'required': True}]
        
        
    def get_output(self):
        return [CorticalSurface, SkinAir, FaceSurface]


    @transactional
    def launch(self, surface_type, data_file):
        """
        Execute import operations:
        """
        try:
            surface = create_surface_of_type(surface_type)
            surface.storage_path = self.storage_path
            surface.set_operation_id(self.operation_id)
            surface.zero_based_triangles = True

            with open(data_file) as f:
                obj = ObjSurface(f)

            surface.vertices = obj.vertices
            surface.triangles = obj.triangles
            if obj.normals:
                surface.vertex_normals = obj.normals
            return [surface]
        except ParseException, excep:
            logger = get_logger(__name__)
            logger.exception(excep)
            raise LaunchException(excep)