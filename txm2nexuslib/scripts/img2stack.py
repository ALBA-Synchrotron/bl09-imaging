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

from txm2nexuslib.images.imagestostack import many_images_to_h5_stack


def main():

    def str2bool(v):
        return v.lower() in ("yes", "true", "t", "1")

    description = ('From many individual image hdf5 files to a single '
                   'hdf5 file containing a stack of images')
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=RawTextHelpFormatter)
    parser.register('type', 'bool', str2bool)

    parser.add_argument('file_index_fn', metavar='file_index_fn',
                        type=str, help='DB index json filename of hdf5 data')

    parser.add_argument('-t', '--table_h5', type=str,
                        default="hdf5_proc",
                        help='DB table of hdf5 images\n'
                             '(default: hdf5_proc)')

    parser.add_argument('-st', '--structure', type=str,
                        default="normalized",
                        help='Type of hdf5 stack structure\n'
                             '(default: normalized)')

    parser.add_argument('-d', '--date', type=int,
                        default=None,
                        help='Date of images in files '
                             'to be put in the stack\n'
                             '(default: None)')

    parser.add_argument('-s', '--sample', type=str,
                        default=None,
                        help='Sample name of images in files '
                             'to be put in the stack\n'
                             '(default: None)')

    parser.add_argument('-e', '--energy', type=float,
                        default=None,
                        help='Energy of images in files '
                             'to be put in the stack\n'
                             '(default: None)')

    parser.add_argument('-z', '--zpz', type=float,
                        default=None,
                        help='Zone Plate Z position of images in files '
                             'to be put in the stack\n'
                             '(default: None)')

    parser.add_argument('-c', '--cores', type=int,
                        default=-2,
                        help='Number of cores used for the format '
                             'conversion\n'
                             '(default: all CPUs but one are used: -2)')

    args = parser.parse_args()
    many_images_to_h5_stack(args.file_index_fn, table_name=args.table_h5,
                            type_struct=args.structure,
                            date=args.date, sample=args.sample,
                            energy=args.energy, zpz=args.zpz,
                            cores=args.cores)


if __name__ == "__main__":
    main()
