#!/usr/bin/python

"""
(C) Copyright 2014-2017 ALBA-CELLS
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

import os
import sys
import argparse
from argparse import RawTextHelpFormatter

from txm2nexuslib.image.image_operate_lib import *

def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


class ImageOperate(object):

    def __init__(self):
        parser = argparse.ArgumentParser(
            description='img allows performing operations with images',
            usage="""img <command> [<args>]

img commands are:
   copy          - Copy hdf5 file to a new hdf5 file for processing
   add           - Addition of many images
                 - Add constant to image
   subtract      - From a reference image (minuend),
                   subtract another image (subtrahend)
                 - Subtract constant to image
                 - Subtract image to constant
   multiply
                 - Multiply many images element-wise
                 - Multiply an image by a constant
   divide
                 - Divide an image by another image, element-wise
                   numerator image divided by denominator image
                 - Divide an image by a constant
                 - Divide a constant by an image
   normalize
                 - Normalize image by single FF, exposure times and
                   machine currents
                 - Normalize image by average FF, exposure times and
                   machine currents
""")
        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print '\nUnrecognized command\n'
            parser.print_help()
            exit(1)
        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def copy(self):
        parser = argparse.ArgumentParser(
            description='Copy a whole hdf5 file to a new file',
            formatter_class=RawTextHelpFormatter)
        parser.add_argument('input', metavar='input_hdf5_filename',
                            type=str, help='input hdf5 filename')
        parser.add_argument('-o', '--output',
                            default='default',
                            metavar='output',
                            type=str, help='output hdf5 filename')
        parser.add_argument('-s', '--suffix',
                            default='_proc',
                            type=str, help='suffix for new file name')
        args = parser.parse_args(sys.argv[2:])
        if args.output == "default":
            base_fn = os.path.splitext(args.input)[0]
            output_fn = base_fn + args.suffix + ".hdf5"
        print ('\nimage_operate copy: from %s to %s\n' % (args.input,
                                                          output_fn))
        copy_h5(args.input, output_fn)

    def add(self):
        parser = argparse.ArgumentParser(
            description='Addition of images\n'
                        'Addition of a constant factor',
            formatter_class=RawTextHelpFormatter)
        parser.add_argument('addends',
                            metavar='addends_hdf5_filenames',
                            type=str,
                            nargs='+', default=None,
                            help='input the addends single image '
                                 'hdf5 files')
        parser.add_argument('-c', '--constant',
                            type=float,
                            default=0,
                            help='constant to be added')
        parser.add_argument('-o', '--output',
                            default='default',
                            metavar='output',
                            type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])

        add(args.addends, constant=args.constant,
            store=True, output_h5_fn=args.output)

    def subtract(self):
        parser = argparse.ArgumentParser(
            description='- From a reference image (minuend), '
                        'subtract one or more images (subtrahends)\n'
                        '- Subtract a constant',
            formatter_class=RawTextHelpFormatter)
        parser.add_argument('minuend_subtrahends',
                            metavar='minuend_subtrahends_hdf5_files',
                            type=str, nargs='+',
                            help='minuend image hdf5 filename followed by '
                                 'the subtrahend image hdf5 filename(s)')
        parser.add_argument('-c', '--constant',
                            type=float,
                            default=0,
                            help='constant to be subtracted')
        parser.add_argument('-o', '--output',
                            default='default',
                            metavar='output',
                            type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])

        subtract(args.minuend_subtrahends, constant=args.constant,
                 store=True, output_h5_fn=args.output)

    def multiply(self):
        parser = argparse.ArgumentParser(
            description='Multiplication of images'
                        'Multiplication by a constant factor',
            formatter_class=RawTextHelpFormatter)
        parser.add_argument('factors',
                            metavar='factors_hdf5_filenames',
                            type=str,
                            nargs='+', default=None,
                            help='input the factors single image '
                                 'hdf5 files')
        parser.add_argument('-c', '--constant',
                            type=float,
                            default=1,
                            help='constant multiplying the resulting image')
        parser.add_argument('-o', '--output',
                            default='default',
                            metavar='output',
                            type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])

        multiply(args.factors, constant=args.constant,
                 store=True, output_h5_fn=args.output)

    def divide(self):
        """Divide two images element-wise"""
        parser = argparse.ArgumentParser(description='Divide element-wise '
                                                     'a numerator image by '
                                                     'a denominator image ',
                                         formatter_class=RawTextHelpFormatter)
        parser.add_argument('numerator', metavar='image1', type=str,
                            help='numerator single image hdf5 file')
        parser.add_argument('denominator', metavar='image2', type=str,
                            help='denominator single image hdf5 file')
        parser.add_argument('-c', '--constant',
                            type=float,
                            default=1,
                            help='constant dividing the resulting image')
        parser.add_argument('-o', '--output',
                    default='default',
                    metavar='output',
                    type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])

        # TODO: implement divide application

        description = "image_operate divide (image division):\n"
        description += (dset_numerator + "@" + str(args.numerator) + " /\n" +
                        dset_denominator + "@" + str(args.denominator))
        print("\n" + description + "\n")

    def normalize(self):
        """
        Normalize BL09 hdf5 image: Normalize image by current, exposure time,
        and FF average image, which at its turn have been normalized also by
        current and exposure time.
        """
        parser = argparse.ArgumentParser(
            description='normalize BL09 image. Use '
                        'exposure times and machine currents'
                        'Inputs:'
                        'image_filename: h5 filename with image to normalize'
                        'ff_filenames: ff h5 filename(s)'
                        'output: (optional) Output filename. If indicated'
                        'the image is stored in a new h5 file',
            formatter_class=RawTextHelpFormatter)
        parser.register('type', 'bool', str2bool)

        parser.add_argument('image_filename', metavar='image_filename',
                            type=str, help='hdf5 filename containing the '
                                           'image to normalize')
        parser.add_argument('ff_filenames', metavar='ff_filenames', type=str,
                            nargs='+', default=None,
                            help='FF single images hdf5 filenames')
        parser.add_argument('-o', '--output',
                            default='default',
                            metavar='output',
                            type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])

        normalize_image(args.image_filename, args.ff_filenames,
                        store_normalized=True, output_h5_fn=args.output)


def main():
    ImageOperate()


if __name__ == '__main__':
    main()
