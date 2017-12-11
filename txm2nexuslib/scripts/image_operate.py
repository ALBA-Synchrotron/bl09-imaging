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

from txm2nexuslib.image.image_operate_lib import *

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

        parser.add_argument('addends',
                            metavar='addends_hdf5_files_list',
                            type=str,
                            nargs='+', default=None,
                            help='input the addends single image '
                                 'hdf5 files')
        args = parser.parse_args(sys.argv[2:])
        print '\nimage_operate add:'
        print(str(sys.argv[2:]) + "\n")
        image_list = args.addends
        img1 = extract_single_image_from_hdf5(image_list[0])
        shape1 = np.shape(img1)
        result_image = np.zeros(shape1)
        for single_img_hdf5_file in args.addends:
            img = extract_single_image_from_hdf5(single_img_hdf5_file)
            result_image = add_images(result_image, img)
        return result_image

    def subtract(self):
        parser = argparse.ArgumentParser(
            description='From a reference image (minuend), '
                        'subtract another image (subtrahend)')

        parser.add_argument('minuend', metavar='minuend_hdf5_file',
                            type=str, help='reference single image hdf5 file')
        parser.add_argument('subtrahend', metavar='subtrahend_hdf5_file',
                            type=str, help='single image hdf5 file to subtract'
                                           'to the reference image')
        args = parser.parse_args(sys.argv[2:])
        print ('\nimage_operate subtract: %s - %s\n' %
               (args.minuend, args.subtrahend))
        minuend_img = extract_single_image_from_hdf5(args.minuend)
        subtrahend_img = extract_single_image_from_hdf5(args.subtrahend)
        result_image = subtract_images(minuend_img, subtrahend_img)
        return result_image

    def add_constant(self):
        """Add a constant to an image. The constant can be positive or
        negative"""
        parser = argparse.ArgumentParser(description='Add a constant to '
                                                     'an image')
        parser.add_argument('image', metavar='image',
                            type=str, help='reference single image hdf5 file')
        parser.add_argument('constant', metavar='constant',
                            type=str, help='constant to be added to the image')
        args = parser.parse_args(sys.argv[2:])
        cte = args.constant
        print ('\nimage_operate add_constant: %s - %s\n' % (args.image, cte))
        image = extract_single_image_from_hdf5(args.image)
        result_image = add_cte_to_image(image, cte)
        return result_image

    def subtract_image_to_constant(self):
        """Subtract image to constant"""
        parser = argparse.ArgumentParser(description='Subtract an image to '
                                                     'a constant value image')
        parser.add_argument('constant', metavar='constant',
                            type=str, help='minuend constant to which an '
                                           'image will be subtracted')
        parser.add_argument('image', metavar='image',
                            type=str, help='subtrahend image hdf5 file')
        args = parser.parse_args(sys.argv[2:])
        cte = args.constant
        print('\nimage_operate subtract_to_constant: '
              '%s - %s\n' % (cte, args.image))
        image = extract_single_image_from_hdf5(args.image)
        result_image = subtract_image_to_cte(cte, image)
        return result_image



def main():
    ImageOperate()

if __name__ == '__main__':
    main()
