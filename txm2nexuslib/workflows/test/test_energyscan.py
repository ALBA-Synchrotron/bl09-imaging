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
import h5py
from unittest import TestCase
from tinydb import TinyDB, Query


class EnergyScanTestCase(TestCase):

    def setUp(self):
        pass

    def test_energyscan(self):
        """Test that energyscan preprocessing is executed with
        a correct exit code"""
        dir_name = "/siciliarep/projects/ctgensoft/BLs/BL09/DATA/TESTS/ESCAN/"
        txm_txt_script = "f14_small.txt"
        fullname_to_txt_script = dir_name + txm_txt_script
        script_call = "energyscan " + fullname_to_txt_script
        exit_code = os.system(script_call)

        # Test that exit code is not error
        expected_exit_code = 0
        self.assertEqual(exit_code, expected_exit_code)

        # Test that dataset shape is equal to the expected shape
        file_index_fn = dir_name + "index.json"
        file_index_db = TinyDB(file_index_fn)
        self.stack_table = file_index_db.table("hdf5_stacks")
        all_file_records = self.stack_table.all()
        for record in all_file_records:
            h5_stack_filename = dir_name + record["filename"]
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

    def tearDown(self):
        pass

