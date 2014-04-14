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
.. moduleauthor:: Calin Pavel <calin.pavel@codemart.ro>
"""

from tvb.adapters.uploaders.abcuploader import ABCUploader
from tvb.adapters.uploaders.constants import OPTION_SURFACE_CORTEX, OPTION_SURFACE_SKINAIR, OPTION_SURFACE_FACE
from tvb.adapters.uploaders.gifti.gifti_parser import GIFTIParser, OPTION_READ_METADATA
from tvb.basic.logger.builder import get_logger
from tvb.core.adapters.exceptions import LaunchException, ParseException
from tvb.datatypes.surfaces import CorticalSurface, SkinAir, FaceSurface



class GIFTISurfaceImporter(ABCUploader):
    """
    This importer is responsible for import of surface from GIFTI format (XML file)
    and store them in TVB as Surface.
    """
    _ui_name = "Surface GIFTI"
    _ui_subsection = "gifti_surface_importer"
    _ui_description = "Import a surface from GIFTI"
    
    def get_upload_input_tree(self):
        """
        Take as input a .GII file.
        """
        return [{'name': 'file_type', 'type': 'select',
                 'label': 'Specify file type : ', 'required': True,
                 'options': [{'name': 'Specified in the file metadata', 'value': OPTION_READ_METADATA},
                             {'name': 'Cortex', 'value': OPTION_SURFACE_CORTEX},
                             {'name': 'Outer Skin', 'value': OPTION_SURFACE_SKINAIR},
                             {'name': 'Face Shade', 'value': OPTION_SURFACE_FACE}],
                 'default': OPTION_READ_METADATA},

                {'name': 'data_file', 'type': 'upload', 'required_type': '.gii', 'required': True,
                 'label': 'Please select file to import (.gii)'},

                {'name': 'data_file_part2', 'type': 'upload', 'required_type': '.gii', 'required': False,
                 'label': 'Please select part 2 of the file to import (.gii)'},

                {'name': 'should_center', 'type': 'bool', 'default': False,
                 'label': 'Center surface using vertex means along axes'}
                ]


    def get_output(self):
        return [CorticalSurface, SkinAir, FaceSurface]


    def launch(self, file_type, data_file, data_file_part2, should_center=False):
        """
        Execute import operations:
        """
        parser = GIFTIParser(self.storage_path, self.operation_id)
        try:
            surface = parser.parse(data_file, data_file_part2, file_type, should_center=should_center)
            return [surface]             
        except ParseException, excep:
            logger = get_logger(__name__)
            logger.exception(excep)
            raise LaunchException(excep)