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


import sys
import argparse
import numpy as np

from txm2nexuslib.image.image_operate_lib import \
    extract_single_image_from_hdf5, add_images

class ImageOperate(object):

    def __init__(self):
        parser = argparse.ArgumentParser(
            description='image_operate allows performing operations '
                        'with images',
            usage="""image_operate <command> [<args>]

The most commonly used image_operate commands are:
   add           Addition of many images
   subtract      From a reference image (minuend),
                 subtract another image (subtrahend)
""")
        parser.add_argument('command', help='Subcommand to run')
        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print '\nUnrecognized command\n'
            parser.print_help()
            exit(1)
        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def add(self):
        parser = argparse.ArgumentParser(
            description='Addition of many images')
        parser.add_argument('-a', '--addends-list', action='append',
                            required=True,
                            metavar='[addends_hdf5_files_list]',
                            help='input the addends single image '
                                 'hdf5 files')
        # prefixing the argument with -- means it's optional
        args = parser.parse_args(sys.argv[2:])
        image_list = args.addends_list

        img1 = extract_single_image_from_hdf5(image_list[0])
        shape1 = np.shape(img1)
        result_image = np.zeros(shape1)

        for single_img_hdf5_file in args.addends_list:
            img = extract_single_image_from_hdf5(single_img_hdf5_file)
            result_image = add_images(result_image, img)

        print '\nRunning image_operate add\n'

    def subtract(self):
        parser = argparse.ArgumentParser(
            description='From a reference image (minuend), '
                        'subtract another image (subtrahend)')
        # NOT prefixing the argument with -- means it's not optional
        parser.add_argument('minuend', metavar='minuend_hdf5_file',
                            type=str, help='reference single image hdf5 file')
        parser.add_argument('subtrahend', metavar='subtrahend_hdf5_file',
                            type=str, help='single image hdf5 file to subtract'
                                           'to the reference image')

        args = parser.parse_args(sys.argv[2:])
        print ('\nRunning image_operate subtract: %s - %s\n' %
               (args.minuend,
                args.subtrahend))


def main():
    ImageOperate()

if __name__ == '__main__':
    main()
