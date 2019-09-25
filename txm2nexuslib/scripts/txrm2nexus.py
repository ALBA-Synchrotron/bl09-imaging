#!/usr/bin/python

"""
(C) Copyright 2014-2017 Marc Rosanes
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


from txm2nexuslib import txrmnex
import datetime
import argparse


def main():

    print("\n")
    print(datetime.datetime.today())
    print("\n")

    parser = argparse.ArgumentParser(
        description='Converts a file from .txrm to a NeXus '
                    'complying .hdf5 file.')

    parser.add_argument('files',
                        metavar='fname',
                        type=str,
                        nargs='+', default=None,
                        help='Tomography, BrightField and DarkField txrm files '
                             'in the order that have to be processed')
    parser.add_argument('-o', '--files_order', type=str, default='sb',
                        help="Indicates the order in which the "
                             "sample file 's', bright fields 'b' "
                             "and dark fields 'd' have to be processed")
    parser.add_argument('-zi', '--zero-deg-in', type=str, default=None,
                        help="Image at 0 degrees taken before "
                             "the tomography acquisition.")
    parser.add_argument('-zf', '--zero-deg-final', type=str, default=None,
                        help="Image at 0 degrees taken at the end of "
                             "the tomography acquisition.")
    parser.add_argument('--title', type=str, default='X-ray tomography',
                        help="Sets the title of the tomography")
    parser.add_argument('--source-name', type=str, default='ALBA',
                        help="Sets the source name")
    parser.add_argument('--source-type', type=str,
                        default='Synchrotron X-ray Source',
                        help="Sets the source type")
    parser.add_argument('--source-probe', type=str, default='x-ray',
                        help="Sets the source probe. Possible options "
                             "are: 'x-ray', 'neutron', 'electron'")
    parser.add_argument('--instrument-name', type=str, default='BL09 @ ALBA',
                        help="Sets the instrument name")
    parser.add_argument('--sample-name', type=str, default='Unknown',
                        help="Sets the sample name")

    args = parser.parse_args()

    nexus = txrmnex.txrmNXtomo(args.files,
                               args.files_order,
                               args.zero_deg_in,
                               args.zero_deg_final,
                               args.title,
                               args.source_name,
                               args.source_type,
                               args.source_probe,
                               args.instrument_name,
                               args.sample_name)

    if nexus.exitprogram != 1:
        nexus.NXtomo_structure()
        nexus.convert_metadata()
        nexus.convert_image_stack()
        
    else:
        return 

    print(datetime.datetime.today())


if __name__ == "__main__":
    main()

