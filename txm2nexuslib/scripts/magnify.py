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

from txm2nexuslib import magnifylib
import argparse


class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass


def main():
    parser = argparse.ArgumentParser(description="Magnification of "
                                                 "a stack of images.\n"
                                                 "Magnification of a "
                                                 "normalized spectroscopic "
                                                 "ALBA-BL09 image stack.",
                                     formatter_class=CustomFormatter)

    parser.add_argument('inputfile', type=str, default=None,
                        help='Enter the hdf5 normalized image stack')
    parser.add_argument('magnificationsfile', type=str, default=None,
                        help='Magnification ratios txt file')
    parser.add_argument('-s', '--spectroscopy', type=int, default=1,
                        help='Magnification of spectroscopy images (-s=1).')

    args = parser.parse_args()

    if args.spectroscopy == 1:
        print("\nMagnifying normalized images\n")
        # Magnification of each of the images of the spectroscopic
        # stack by a given ratio.
        magnify_object = magnifylib.Magnify(args.inputfile,
                                            args.magnificationsfile,
                                            args.spectroscopy)
        magnify_object.magnify_spectrum()


if __name__ == "__main__":
    main()
