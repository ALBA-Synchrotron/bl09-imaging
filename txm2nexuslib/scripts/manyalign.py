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

from txm2nexuslib.images.multiplealign import align_images


def main():

    def str2bool(v):
        return v.lower() in ("yes", "true", "t", "1")

    description = ('Normalize images located in different hdf5 files\n'
                   'Each file containing one of the images to be normalized')
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=RawTextHelpFormatter)
    parser.register('type', 'bool', str2bool)

    parser.add_argument('file_index_fn', metavar='file_index_fn',
                        type=str, help='DB index json filename of hdf5 data '
                                       'files to be normalized')

    parser.add_argument('-t', '--table_h5', type=str,
                        default="hdf5_proc",
                        help='DB table of hdf5 to be normalized\n'
                             '(default: hdf5_proc)')

    parser.add_argument('-r', '--roi_size',
                        type=float,
                        default=0.5,
                        help='Tant per one, of the total amount of image '
                             'pixels. \nIt determines the ROI size used'
                             'in the alignment')

    parser.add_argument('-da', '--dataset_for_aligning',
                        type=str,
                        default="data",
                        help='dataset containing the image to be aligned\n'
                             'Default: data')
    parser.add_argument('-dr', '--dataset_reference',
                        type=str,
                        default="data",
                        help='dataset containing the reference dataset\n'
                             'Default: data')

    parser.add_argument('-v', '--variable',
                        type=str,
                        default="zpz",
                        help='Variable to align regarding to it\n'
                             'Default: zpz')

    parser.add_argument('-d', '--date', type=int,
                        default=None,
                        help='Date of files to be normalized\n'
                             'If None, no filter is applied\n'
                             '(default: None)')

    parser.add_argument('-s', '--sample', type=str,
                        default=None,
                        help='Sample name of files to be normalized\n'
                             'If None, all sample names are normalized\n'
                             '(default: None)')

    parser.add_argument('-e', '--energy', type=float,
                        default=None,
                        help='Energy of files to be normalized\n'
                             'If None, no filter is applied\n'
                             '(default: None)')

    parser.add_argument('-c', '--cores', type=int,
                        default=-2,
                        help='Number of cores used for the format conversion\n'
                             '(default is max of available CPUs but one: -2)')

    args = parser.parse_args()

    align_images(args.file_index_fn, args.table_h5,
                 dataset_for_aligning=args.dataset_for_aligning,
                 dataset_reference=args.dataset_reference,
                 roi_size=args.roi_size, variable=args.variable,
                 date=args.date, sample=args.sample, energy=args.energy,
                 cores=args.cores)


if __name__ == "__main__":
    main()
