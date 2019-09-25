#!/usr/bin/env python

#############################################################################
##
# This file is part of bl09-imaging (formerly txrm2nexus)
##
# Copyright 2019 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
# bl09-imaging is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# bl09-imaging is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
##
# You should have received a copy of the GNU Lesser General Public License
# along with Taurus.  If not, see <http://www.gnu.org/licenses/>.
##
#############################################################################

import os
import subprocess
import h5py
import time
from git import Repo
from unittest import TestCase
from tinydb import TinyDB, Query
from parameterized import parameterized, parameterized_class


class WorkflowTestCase(TestCase):

    @classmethod
    def setUpClass(self):
        self.relative_dir_name = "/tmp/TEST_DATA"
        os.system("mkdir -p " + self.relative_dir_name)
        if not os.listdir(self.relative_dir_name):
            git_url = "https://git.cells.es/controls/bl09_test_images.git"
            Repo.clone_from(git_url, self.relative_dir_name)

    @parameterized.expand([
        ('f14_small.txt', 'energyscan', None, "Escan_test_imgs",
         dict(h5_main_grp="SpecNormalized",
              h5_dataset="spectroscopy_normalized",
              expected_shape=(2, 974, 984))
         ),
        ('dichro_test.txt', 'magnetism', "--db --ff --th --stack",
         "magnetism_test_imgs",
         dict(h5_main_grp="TomoNormalized",
              h5_dataset="TomoNormalized",
              expected_shape=(2, 974, 984))
         ),
        ('ctbio_single_zp.txt', 'ctbio', "-m=False", "ctbio_test_imgs",
         dict(h5_main_grp="TomoNormalized",
              h5_dataset="TomoNormalized",
              expected_shape=(3, 974, 984))
         )])
    def test_check_workflow(self, txm_txt_script=None, workflow_script=None,
                            script_args=None, images_dir=None,
                            h5_tree=None):
        """Test for BL09 offline workflows"""

        data_dir_name = os.path.join(self.relative_dir_name,
                                           images_dir)
        fullname_to_txt_script = os.path.join(data_dir_name,
                                              txm_txt_script)
        print(fullname_to_txt_script)

        if script_args is None:
            script_call = "{} {}".format(workflow_script,
                                         fullname_to_txt_script)
        else:
            script_call = "{} {} {}".format(workflow_script,
                                            fullname_to_txt_script,
                                            script_args)
        exit_code = os.system(script_call)

        # Test that energyscan preprocessing is executed with
        # a correct exit code
        expected_exit_code = 0
        self.assertEqual(exit_code, expected_exit_code)
        if h5_tree:
            self._validate_dataset_dims(data_dir_name, h5_tree)

    def _validate_dataset_dims(self, data_dir_name, h5_tree):
        # Test that dataset shape is equal to the expected shape
        file_index_fn = os.path.join(data_dir_name, "index.json")
        file_index_db = TinyDB(file_index_fn)
        stack_table = file_index_db.table("hdf5_stacks")
        all_file_records = stack_table.all()
        for record in all_file_records:
            h5_stack_filename = os.path.join(data_dir_name,
                                             record["filename"])
            f = h5py.File(h5_stack_filename, "r")
            h5_main_grp = h5_tree["h5_main_grp"]
            h5_dataset = h5_tree["h5_dataset"]
            dataset_shape = f[h5_main_grp][h5_dataset].shape
            expected_shape = h5_tree['expected_shape']
            dataset_shape_str = str(dataset_shape)
            expected_shape_str = str(expected_shape)
            err_msg = ("Dataset shape %s, is different than \n "
                       "expected shape %s" % (dataset_shape_str,
                                              expected_shape_str))
            self.assertEqual(dataset_shape, expected_shape, err_msg)

    @classmethod
    def tearDownClass(self):
        abs_path_data_folder = os.path.abspath(self.relative_dir_name)
        subprocess.call(["rm", "-rf", "{}".format(abs_path_data_folder)])



