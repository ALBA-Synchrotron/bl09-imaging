#!/usr/bin/python

"""
(C) Copyright 2017 Marc Rosanes
The program is distributed under the terms of the
GNU General Public License (or the Lesser GPL).

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import numpy as np
import h5py


class Magnify:

    def __init__(self, inputfile, magnificationsfile, spectroscopy):

        self.filename_nexus = inputfile
        self.magnifications_ratios_file = magnificationsfile
        self.spectroscopy = spectroscopy

        self.input_nexusfile = h5py.File(self.filename_nexus, 'r')
        self.outputfilehdf5 = inputfile.rsplit('.', 1)[0] + '_magnified.hdf5'
        self.tomonorm = h5py.File(self.outputfilehdf5, 'w')
        self.norm_grp = self.tomonorm.create_group("SpecNormalized")
        self.norm_grp.attrs['NX_class'] = "NXentry"

        return

    def magnify_spectrum(self):
        pass
