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
from unittest import TestCase


class EnergyScanTestCase(TestCase):

    def setUp(self):
        pass

    def test_energyscan(self):
        dir_name = "/siciliarep/projects/ctgensoft/BLs/BL09/DATA/TESTS/ESCAN/"
        txm_txt_script = "f14_small.txt"
        fullname_to_txt_script = dir_name + txm_txt_script
        script_call = "energyscan " + fullname_to_txt_script
        exit_code = os.system(script_call)
        self.assertEqual(exit_code, 0)

    def tearDown(self):
        pass

