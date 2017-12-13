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
import numpy as np

from txm2nexuslib.image.image_operate_lib import *

class ImageOperate(object):

    def __init__(self):
        parser = argparse.ArgumentParser(
            description='image_operate allows performing operations '
                        'with images',
            usage="""image_operate <command> [<args>]

image_operate commands are:
   copy          Copy hdf5 file to a new hdf5 file for processing
   add           Addition of many images
   subtract      From a reference image (minuend),
                 subtract another image (subtrahend)
   add_constant  Add a constant to an image (the constant can be
                 positive or negative)
   subtract_image_to_constant
                 Subtract an image to a constant
   multiply_by_constant
                 Multiply an image by a constant
   divide_by_constant
                 Divide an image by a constant
   multiply_element_wise
                 Multiply two images element-wise
   divide_element_wise
                 Divide an image by another image, element-wise
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
            description='Copy a whole hdf5 file to a new file')
        parser.add_argument('input', metavar='input_hdf5_filename',
                            type=str, help='input hdf5 filename')
        parser.add_argument('-o', '--output',
                            default='default',
                            metavar='output',
                            type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])
        if args.output == "default":
            base_fn = os.path.splitext(args.input)[0]
            output_fn = base_fn + "_proc.hdf5"
        print ('\nimage_operate copy: from %s to %s\n' % (args.input,
                                                          output_fn))
        copy_hdf5(args.input, output_fn)

    def add(self):
        parser = argparse.ArgumentParser(
            description='Addition of many images')
        parser.add_argument('-o', '--output',
                            default='default',
                            metavar='output',
                            type=str, help='output hdf5 filename')
        parser.add_argument('addends',
                            metavar='addends_hdf5_files_list',
                            type=str,
                            nargs='+', default=None,
                            help='input the addends single image '
                                 'hdf5 files')
        args = parser.parse_args(sys.argv[2:])
        print '\nimage_operate add:'
        print(str(args.addends) + "\n")
        image_list = args.addends
        f_handler = h5py.File(image_list[0], "r")
        img1, _ = extract_single_image_from_hdf5(f_handler)
        shape1 = np.shape(img1)
        result_image = np.zeros(shape1)
        f_handler.close()
        description = "image addition:\n"
        for single_img_hdf5_file in args.addends:
            f_handler = h5py.File(single_img_hdf5_file, "r")
            img, dataset = extract_single_image_from_hdf5(f_handler)
            result_image = add_images(result_image, img)
            f_handler.close()
            description += dataset + "@" + str(single_img_hdf5_file)
            if single_img_hdf5_file is not args.addends[-1]:
                description += " + \n"
        if args.output == "default":
            for single_img_hdf5_file in args.addends:
                store_single_image_in_existing_hdf5(single_img_hdf5_file,
                                                    result_image,
                                                    description=description)
        else:
                store_single_image_in_new_hdf5(args.output,
                                               result_image,
                                               description=description)

    def subtract(self):
        parser = argparse.ArgumentParser(
            description='From a reference image (minuend), '
                        'subtract another image (subtrahend)')
        parser.add_argument('minuend', metavar='minuend_hdf5_file',
                            type=str, help='reference single image hdf5 file')
        parser.add_argument('subtrahend', metavar='subtrahend_hdf5_file',
                            type=str, help='single image hdf5 file to subtract'
                                           'to the reference image')
        parser.add_argument('-o', '--output',
                            default='default',
                            metavar='output',
                            type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])
        print ('\nimage_operate subtract: %s - %s\n' %
               (args.minuend, args.subtrahend))

        f_minuend = h5py.File(args.minuend, "r")
        minuend_img, dset_minuend = \
            extract_single_image_from_hdf5(f_minuend)
        f_subtrahend = h5py.File(args.subtrahend, "r")
        subtrahend_img, dset_subtrahend = \
            extract_single_image_from_hdf5(f_subtrahend)
        result_image = subtract_images(minuend_img, subtrahend_img)
        f_minuend.close()
        f_subtrahend.close()
        description = "image subtraction:\n"
        description += (dset_minuend + "@" + str(args.minuend) + "-\n" +
                        dset_subtrahend + "@" + str(args.subtrahend))
        if args.output == "default":
            store_single_image_in_existing_hdf5(args.minuend,
                                                result_image,
                                                description=description)
            store_single_image_in_existing_hdf5(args.subtrahend,
                                                result_image,
                                                description=description)
        else:
                store_single_image_in_new_hdf5(args.output,
                                               result_image,
                                               description=description)


    def add_constant(self):
        """Add a constant to an image. The constant can be positive or
        negative"""
        parser = argparse.ArgumentParser(description='Add a constant to '
                                                     'an image')
        parser.add_argument('image', metavar='image',
                            type=str, help='reference single image hdf5 file')
        parser.add_argument('constant', metavar='constant',
                            type=str, help='constant to be added to the image')
        parser.add_argument('-o', '--output',
                    default='out.hdf5',
                    metavar='output',
                    type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])
        cte = args.constant
        print ('\nimage_operate add_constant: %s + %s\n' % (args.image, cte))
        image = extract_single_image_from_hdf5(args.image)
        result_image = add_cte_to_image(image, cte)
        store_single_image_in_hdf5(args.output, result_image)

    def subtract_image_to_constant(self):
        """Subtract image to constant"""
        parser = argparse.ArgumentParser(description='Subtract an image to '
                                                     'a constant value image')
        parser.add_argument('constant', metavar='constant',
                            type=str, help='minuend constant to which an '
                                           'image will be subtracted')
        parser.add_argument('image', metavar='image',
                            type=str, help='subtrahend image hdf5 file')
        parser.add_argument('-o', '--output',
                    default='out.hdf5',
                    metavar='output',
                    type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])
        cte = args.constant
        print('\nimage_operate subtract_image_to_constant: '
              '%s - %s\n' % (cte, args.image))
        image = extract_single_image_from_hdf5(args.image)
        result_image = subtract_image_to_cte(cte, image)
        store_single_image_in_hdf5(args.output, result_image)

    def multiply_by_constant(self):
        """Multiply an image by a constant"""
        parser = argparse.ArgumentParser(description='Multiply an image by a '
                                                     'constant')
        parser.add_argument('image', metavar='image',
                            type=str, help='single image hdf5 file')
        parser.add_argument('constant', metavar='constant',
                            type=str, help='constant by which the image '
                                           'will be multiplied')
        parser.add_argument('-o', '--output',
                    default='out.hdf5',
                    metavar='output',
                    type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])
        cte = float(args.constant)
        print ('\nimage_operate multiply_by_constant: %s * %s\n' %
               (args.image, cte))
        image = extract_single_image_from_hdf5(args.image)
        result_image = multiply_image_by_constant(image, cte)
        store_single_image_in_hdf5(args.output, result_image)

    def divide_by_constant(self):
        """Divide an image by a constant"""
        parser = argparse.ArgumentParser(description='Divide an image by a '
                                                     'constant')
        parser.add_argument('image', metavar='image',
                            type=str, help='single image hdf5 file')
        parser.add_argument('constant', metavar='constant',
                    type=str, help='constant by which the image will be '
                                   'divided')
        parser.add_argument('-o', '--output',
                    default='out.hdf5',
                    metavar='output',
                    type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])
        cte = float(args.constant)
        print ('\nimage_operate divide_by_constant: %s / %s\n' %
               (args.image, cte))
        image = extract_single_image_from_hdf5(args.image)
        result_image = divide_image_by_constant(image, cte)
        store_single_image_in_hdf5(args.output, result_image)

    def multiply_element_wise(self):
        """Multiply two images element-wise"""
        parser = argparse.ArgumentParser(description='Multiply an image by '
                                                     'another image')
        parser.add_argument('image1', metavar='image1', type=str,
                            help='single first image hdf5 file')
        parser.add_argument('image2', metavar='image2', type=str,
                            help='single second image hdf5 file')
        parser.add_argument('-o', '--output',
                    default='out.hdf5',
                    metavar='output',
                    type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])
        print ('\nimage_operate multiply_element_wise: %s * %s\n' %
               (args.image1, args.image2))
        image1 = extract_single_image_from_hdf5(args.image1)
        image2 = extract_single_image_from_hdf5(args.image2)
        result_image = multiply_images_element_wise(image1, image2)
        store_single_image_in_hdf5(args.output, result_image)

    def divide_element_wise(self):
        """Divide two images element-wise"""
        parser = argparse.ArgumentParser(description='Divide a numerator '
                                                     'image by a denominator '
                                                     'image')
        parser.add_argument('numerator', metavar='image1', type=str,
                            help='numerator single image hdf5 file')
        parser.add_argument('denominator', metavar='image2', type=str,
                            help='denominator single image hdf5 file')
        parser.add_argument('-o', '--output',
                    default='out.hdf5',
                    metavar='output',
                    type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])
        print ('\nimage_operate divide_element_wise: %s / %s\n' %
               (args.numerator, args.denominator))
        numerator = extract_single_image_from_hdf5(args.numerator)
        denominator = extract_single_image_from_hdf5(args.denominator)
        result_image = divide_images_element_wise(numerator, denominator)
        store_single_image_in_hdf5(args.output, result_image)


def main():
    ImageOperate()


if __name__ == '__main__':
    main()
