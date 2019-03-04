#!/usr/bin/env python

#############################################################################
##
# This file is part of txrm2nexus
##
# Copyright 2019 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
# txrm2nexus is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# txrm2nexus is distributed in the hope that it will be useful,
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


class EnergyScanTestCase(TestCase):

    @classmethod
    def setUpClass(self):
        self.relative_dir_name = "/tmp/TEST_DATA"
        os.system("mkdir -p " + self.relative_dir_name)
        self.escan_data_dir_name = (self.relative_dir_name +
                                    "/Escan_test_imgs/")

        if not os.listdir(self.relative_dir_name):
            git_url = "https://git.cells.es/controls/bl09_test_images.git"
            Repo.clone_from(git_url, self.relative_dir_name)

    def test_energyscan(self):
        """Test for energyscan offline workflow"""

        txm_txt_script = "f14_small.txt"
        fullname_to_txt_script = self.escan_data_dir_name + txm_txt_script
        print(fullname_to_txt_script)

        script_call = "energyscan " + fullname_to_txt_script
        exit_code = os.system(script_call)

        # Test that energyscan preprocessing is executed with
        # a correct exit code
        expected_exit_code = 0
        self.assertEqual(exit_code, expected_exit_code)

        # Test that dataset shape is equal to the expected shape
        file_index_fn = self.escan_data_dir_name + "index.json"
        file_index_db = TinyDB(file_index_fn)
        self.stack_table = file_index_db.table("hdf5_stacks")
        all_file_records = self.stack_table.all()
        for record in all_file_records:
            h5_stack_filename = self.escan_data_dir_name + record["filename"]
            f = h5py.File(h5_stack_filename, "r")
            dataset_shape = f["SpecNormalized"][
                "spectroscopy_normalized"].shape
            expected_shape = (2, 974, 984)
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



