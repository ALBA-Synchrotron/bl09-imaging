#!/usr/bin/python

"""
(C) Copyright 2018 ALBA-CELLS
Author: Marc Rosanes Siscart
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


import time
import subprocess
import argparse
from argparse import RawTextHelpFormatter


def main():
    """
    - Convert from xrm to hdf5 individual image hdf5 files
    - Copy raw hdf5 to new files for processing
    - Crop borders
    - Normalize
    - Create stacks by date, sample, energy and zpz,
      with multiple angles in each stack
    """
    def str2bool(v):
        return v.lower() in ("yes", "true", "t", "1")

    description = ('From xrm to cropped and normalized individual image '
                   'hdf5 files and create stacks from them.'
                   'The outputs are single energy, single'
                   'zpz, multiple angles, image stacks')
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=RawTextHelpFormatter)
    parser.register('type', 'bool', str2bool)

    parser.add_argument('txm_txt_script', type=str,
                        help='TXM txt script containing the commands used'
                             'to perform the image acquisition by the '
                             'BL09 TXM microscope')

    parser.add_argument('-db', '--db_file_index', type=str,
                        default="index.json",
                        help='DB file index, containing the image filenames '
                             'and metadata about the acquisition '
                             'of these images')

    parser.add_argument('--crop', type='bool',
                        default='True',
                        help='- If True: Crop images\n'
                             '- If False: Do not crop images\n'
                             '(default: True)')

    args = parser.parse_args()

    start_time = time.time()
    subprocess.call(["manyxrm2h5", args.txm_txt_script])
    subprocess.call(["copy2proc", args.db_file_index])
    if args.crop:
        subprocess.call(["manycrop", args.db_file_index])
    subprocess.call(["manynorm", args.db_file_index])
    subprocess.call(["img2stack", args.db_file_index])
    print("\nmanyxrm2norm took %d seconds\n" % (time.time() - start_time))


if __name__ == "__main__":
    main()
