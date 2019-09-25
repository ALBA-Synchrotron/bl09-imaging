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


import argparse
from argparse import RawTextHelpFormatter

from txm2nexuslib import tomonorm
from txm2nexuslib import specnorm
from txm2nexuslib import mosaicnorm


class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass


def main():
    parser = argparse.ArgumentParser(
        description="Normalization of:"
                    + "\n- TOMOGRAPHIES for single energy & single focus"
                    + "\n- SPECTROSCOPIES"
                    + "\nTaking into account FF, currents and exposure times",
        formatter_class=RawTextHelpFormatter)

    parser.add_argument('inputfile', type=str, default=None,
                        help='Enter hdf5 file containing the'
                             + '\ninformation of tomography data, flatfield,'
                             + '\nand optionally darkfield.')

    parser.add_argument('-s', '--spectroscopy', type=int, default=0,
                        help='Constant energy tomo normalization (-s=0)'
                             + '\nor spectroscopy normalization (-s=1).'
                             + '\nDefault: -s=0.')

    parser.add_argument('-d', '--darkfield', type=int, default=0,
                        help='Normalize using also a DarkField'
                             + '\nDefault: -d=0.')

    parser.add_argument('-g', '--gaussianblur', type=int, default=0,
                        help='gaussian filtering for avoiding '
                             + 'diffraction artifacts.'
                             + '\nDefault=0 -> gaussian filter not applied.'
                             + '\nInteger not 0: Indicate the std as integer. '
                             + '\nE.g.: -g=5')

    parser.add_argument('-f', '--avgff', type=int, default=1,
                        help='Normalize using avergeFF (-f=1)'
                             + '\nor using single FF (FFimage 0)'
                             + '\n(Default: -f=1).')

    parser.add_argument('-m', '--mosaicnorm', type=int, default=0,
                        help='Mosaic normalization using a given FF (-m=1).')
    
    parser.add_argument('-r', '--ratio', type=int, default=1,
                        help='ratio = exp_time_mosaic/exp_time_FF.'
                             + '\nExposure times ratio. '
                             + '\nThis option can be used only when '
                             + 'normalizing mosaics.')
               
    parser.add_argument('-a', '--avgtomnorm', type=int, default=0,
                        help='Indicate if we want to obtain the average of'
                             + '\nthe normalized images (-a=1).'
                             + '\nAvailable only for Tomo normalization.')

    parser.add_argument('-di',
                        '--diffraction',
                        type=int,
                        default=0,
                        help='Correct diffraction pattern by passing'
                             + '\nan external avgFF (-d=1).')

    args = parser.parse_args()

    if args.mosaicnorm == 1:
        print("\nNormalizing Mosaic")
        normalize_object = mosaicnorm.MosaicNormalize(args.inputfile,
                                                      ratio=args.ratio)
        normalize_object.normalizeMosaic()  
        
    else:
        if args.spectroscopy == 0:
            print("\nNormalizing Tomography images")
            """ We normalize the tomography using the tomography images,
            the FF (flatfield) images, the experimental times of FF, images, 
            and the machine current for each image."""
            normalize_object = tomonorm.TomoNormalize(
                args.inputfile, args.darkfield, args.avgtomnorm,
                args.gaussianblur, args.avgff, args.diffraction)
            normalize_object.normalize_tomo()
        else:
            print("\nNormalizing Spectroscopy images")
            normalize_object = specnorm.SpecNormalize(args.inputfile)
            normalize_object.normalizeSpec()

  
if __name__ == "__main__":
    main()



