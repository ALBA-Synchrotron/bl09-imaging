#!/usr/bin/python

"""
(C) Copyright 2018 ALBA-CELLS
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


import argparse
from argparse import RawTextHelpFormatter

from txm2nexuslib.images.multiplexrm2h5 import multiple_xrm_2_hdf5
from txm2nexuslib.parser import create_db, get_db_path


def main():

    def str2bool(v):
        return v.lower() in ("yes", "true", "t", "1")

    description = 'Convert single image xrm files into single image hdf5 ' \
                  'files'
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=RawTextHelpFormatter)
    parser.register('type', 'bool', str2bool)

    parser.add_argument('txm_txt_script', metavar='txm_txt_script',
                        type=str, help='TXM txt script used to create the '
                                       'xrm files')

    parser.add_argument('-s', '--subfolders', type='bool',
                        default='False',
                        help='- If True: Use subfolders for indexing\n'
                             '- If False: Use general folder for indexing\n'
                             '(default: False)')

    parser.add_argument('-c', '--cores', type=int,
                        default=-2,
                        help='Number of cores used for the format conversion\n'
                             '(default is max of available CPUs: -1)')

    parser.add_argument('-u', '--update_db', type='bool',
                        default='True',
                        help='Update DB with hdf5 records\n'
                             '(default: True)')

    args = parser.parse_args()

    db_filename = get_db_path(args.txm_txt_script)
    create_db(args.txm_txt_script)

    multiple_xrm_2_hdf5(db_filename, subfolders=args.subfolders,
                        cores=args.cores, update_db=args.update_db)


if __name__ == "__main__":
    main()



