#!/usr/bin/python

"""
(C) Copyright 2017 ALBA-CELLS
Authors: Marc Rosanes, Carlos Falcon, Zbigniew Reszela, Carlos Pascual
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

import os
import argparse
from argparse import RawTextHelpFormatter
from txm2nexuslib.image.xrm2hdf5 import Xrm2H5Converter


def main():

    description = 'Convert a single image xrm file to a ' \
                  'single image hdf5 file'
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=RawTextHelpFormatter)

    parser.add_argument('xrm_filename', metavar='xrm_filename',
                        type=str, help='xrm filename to be converted '
                                       'to hdf5 format')

    parser.add_argument('-o', '--output-hdf5', type=str, default=None,
                        help='Filename of the output hdf5 file. If not '
                             'given it will keep the input name with the hdf5'
                             'extension')

    args = parser.parse_args()

    xrm2h5_converter = Xrm2H5Converter(args.xrm_filename)
    xrm2h5_converter.convert_xrm_to_h5_file()


if __name__ == "__main__":
    main()

