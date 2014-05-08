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
Testing linking datatypes between projects.
.. moduleauthor:: Mihai Andrei <mihai.andrei@codemart.ro>
"""
import unittest
from tvb.adapters.exporters.export_manager import ExportManager
from tvb.core.entities.file.files_helper import TvbZip
from tvb.core.entities.storage import dao
from tvb.core.services.flow_service import FlowService
from tvb.core.services.project_service import ProjectService
from tvb.core.services.import_service import ImportService
from tvb.core.entities.transient.structure_entities import DataTypeMetaData
from tvb.tests.framework.core.base_testcase import TransactionalTestCase
from tvb.tests.framework.core.test_factory import TestFactory
from tvb.tests.framework.datatypes.datatypes_factory import DatatypesFactory
from tvb.tests.framework.datatypes.datatype1 import Datatype1
from tvb.tests.framework.datatypes.datatype2 import Datatype2


class _BaseLinksTest(TransactionalTestCase):
    GEORGE1st = "george the grey"
    GEORGE2nd = "george"

    def setUpTVB(self):
        """
        Creates a user, an algorithm and 2 projects
        Project src_project will have an operation and 2 datatypes
        Project dest_project will be empty.
        Initializes a flow and a project service
        """
        datatype_factory = DatatypesFactory()
        self.user = datatype_factory.user
        self.src_project = datatype_factory.project

        self.red_datatype = datatype_factory.create_simple_datatype(subject=self.GEORGE1st)
        self.blue_datatype = datatype_factory.create_datatype_with_storage(subject=self.GEORGE2nd)

        # create the destination project
        self.dest_project = TestFactory.create_project(admin=datatype_factory.user, name="destination")

        self.flow_service = FlowService()
        self.project_service = ProjectService()

    def tearDown(self):
        self.clean_database(delete_folders=True)

    def red_datatypes_in(self, project_id):
        return self.flow_service.get_available_datatypes(project_id, Datatype1)[1]

    def blue_datatypes_in(self, project_id):
        return self.flow_service.get_available_datatypes(project_id, Datatype2)[1]



class LinksTest(_BaseLinksTest):
    """
    Test case for datatype linking functionality
    """
    def assertRedsInDest(self, count):
        self.assertEqual(count, self.red_datatypes_in(self.dest_project.id))

    def test_create_link(self):
        dest_id = self.dest_project.id
        self.assertEqual(0, self.red_datatypes_in(dest_id))
        self.flow_service.create_link([self.red_datatype.id], dest_id)
        self.assertEqual(1, self.red_datatypes_in(dest_id))
        self.assertEqual(0, self.blue_datatypes_in(dest_id))

    def test_remove_link(self):
        dest_id = self.dest_project.id
        self.assertEqual(0, self.red_datatypes_in(dest_id))
        self.flow_service.create_link([self.red_datatype.id], dest_id)
        self.assertEqual(1, self.red_datatypes_in(dest_id))
        self.flow_service.remove_link(self.red_datatype.id, dest_id)
        self.assertEqual(0, self.red_datatypes_in(dest_id))

    def test_link_appears_in_project_structure(self):
        dest_id = self.dest_project.id
        self.flow_service.create_link([self.red_datatype.id], dest_id)
        # Test getting information about linked datatypes, from low level methods to the one used by the UI
        dt_1s = dao.get_linked_datatypes_for_project(dest_id)
        self.assertEqual(1, len(dt_1s))
        self.assertEqual(1, self.red_datatypes_in(dest_id))
        json = self.project_service.get_project_structure(self.dest_project, None, DataTypeMetaData.KEY_STATE,
                                                          DataTypeMetaData.KEY_SUBJECT, None)
        self.assertTrue(self.red_datatype.gid in json)

    def test_remove_entity_with_links_moves_links(self):
        dest_id = self.dest_project.id
        self.flow_service.create_link([self.red_datatype.id], dest_id)
        self.assertEqual(1, self.red_datatypes_in(dest_id))
        # remove original datatype
        self.project_service.remove_datatype(self.src_project.id, self.red_datatype.gid)
        # self.project_service.get_datatype_by_id(self.red_datatype.gid)
        # datatype has been moved to one of it's links
        self.assertEqual(1, self.red_datatypes_in(dest_id))
        # project dest no longer has a link but owns the data type
        dt_links = dao.get_linked_datatypes_for_project(dest_id)
        self.assertEqual(0, len(dt_links))


class ImportExportProjectWithLinksTest(_BaseLinksTest):
    def setUpTVB(self):
        """
        Adds to the _BaseLinksTest setup the following
        2 links from src to dest project
        Import/export services
        """
        _BaseLinksTest.setUpTVB(self)
        dest_id = self.dest_project.id
        self.flow_service.create_link([self.red_datatype.id], dest_id)
        self.flow_service.create_link([self.blue_datatype.id], dest_id)
        self.export_mng = ExportManager()
        self.import_service = ImportService()

    def test_export(self):
        export_file = self.export_mng.export_project(self.dest_project)
        with TvbZip(export_file) as z:
            self.assertTrue('links-to-external-projects/Operation.xml' in z.namelist())

    def _export_and_remove_dest(self):
        """export the destination project and remove it"""
        dest_id = self.dest_project.id
        export_file = self.export_mng.export_project(self.dest_project)
        self.project_service.remove_project(dest_id)
        return export_file

    def _import_dest(self, export_file):
        self.import_service.import_project_structure(export_file, self.user.id)
        return self.import_service.created_projects[0].id

    def test_links_recreated_on_import(self):
        export_file = self._export_and_remove_dest()
        imported_proj_id = self._import_dest(export_file)
        self.assertEqual(1, self.red_datatypes_in(imported_proj_id))
        self.assertEqual(1, self.blue_datatypes_in(imported_proj_id))
        links = dao.get_linked_datatypes_for_project(imported_proj_id)
        self.assertEqual(2, len(links))

    def test_datatypes_recreated_on_import(self):
        export_file = self._export_and_remove_dest()
        self.project_service.remove_project(self.src_project.id)
        # both projects have been deleted
        # import should recreate links as datatypes
        imported_proj_id = self._import_dest(export_file)
        self.assertEqual(1, self.red_datatypes_in(imported_proj_id))
        self.assertEqual(1, self.blue_datatypes_in(imported_proj_id))
        links = dao.get_linked_datatypes_for_project(imported_proj_id)
        self.assertEqual(0, len(links))

    def test_datatypes_and_links_recreated_on_import(self):
        export_file = self._export_and_remove_dest()
        # remove datatype 2 from source project
        self.project_service.remove_datatype(self.src_project.id, self.blue_datatype.gid)
        imported_proj_id = self._import_dest(export_file)
        # both datatypes should be recreated
        self.assertEqual(1, self.red_datatypes_in(imported_proj_id))
        self.assertEqual(1, self.blue_datatypes_in(imported_proj_id))
        # only datatype 1 should be a link
        links = dao.get_linked_datatypes_for_project(imported_proj_id)
        self.assertEqual(1, len(links))
        self.assertEquals(self.red_datatype.gid, links[0].gid)


def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(LinksTest))
    test_suite.addTest(unittest.makeSuite(ImportExportProjectWithLinksTest))
    return test_suite


if __name__ == "__main__":
    #So you can run tests from this package individually.
    TEST_RUNNER = unittest.TextTestRunner()
    TEST_SUITE = suite()
    TEST_RUNNER.run(TEST_SUITE)
