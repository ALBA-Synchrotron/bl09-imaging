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
   multiply
                 Multiply many images element-wise
   divide
                 Divide an image by another image, element-wise
                 numerator image divided by denominator image
   add_constant  Add a constant to an image (the constant can be
                 positive or negative)
   subtract_image_to_constant
                 Subtract an image to a constant
   multiply_by_constant
                 Multiply an image by a constant
   divide_by_constant
                 Divide an image by a constant

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
        parser.add_argument('-s', '--suffix',
                            default='_proc',
                            type=str, help='suffix for new file name')
        args = parser.parse_args(sys.argv[2:])
        if args.output == "default":
            base_fn = os.path.splitext(args.input)[0]
            output_fn = base_fn + args.suffix + ".hdf5"
        print ('\nimage_operate copy: from %s to %s\n' % (args.input,
                                                          output_fn))
        copy_hdf5(args.input, output_fn)

    def add(self):
        parser = argparse.ArgumentParser(
            description='Addition of many images')
        parser.add_argument('addends',
                            metavar='addends_hdf5_files_list',
                            type=str,
                            nargs='+', default=None,
                            help='input the addends single image '
                                 'hdf5 files')
        parser.add_argument('-o', '--output',
                            default='default',
                            metavar='output',
                            type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])
        image_list = args.addends
        f_handler = h5py.File(image_list[0], "r")
        img1, _ = extract_single_image_from_hdf5(f_handler)
        shape1 = np.shape(img1)
        result_image = np.zeros(shape1)
        f_handler.close()
        description = "image_operate add (image addition):\n"
        for single_img_hdf5_file in args.addends:
            f_handler = h5py.File(single_img_hdf5_file, "r")
            img, dataset = extract_single_image_from_hdf5(f_handler)
            result_image = add_images(result_image, img)
            f_handler.close()
            description += dataset + "@" + str(single_img_hdf5_file)
            if single_img_hdf5_file is not args.addends[-1]:
                description += " + \n"
        print("\n" + description + "\n")
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
        f_minuend = h5py.File(args.minuend, "r")
        minuend_img, dset_minuend = \
            extract_single_image_from_hdf5(f_minuend)
        f_subtrahend = h5py.File(args.subtrahend, "r")
        subtrahend_img, dset_subtrahend = \
            extract_single_image_from_hdf5(f_subtrahend)
        result_image = subtract_images(minuend_img, subtrahend_img)
        f_minuend.close()
        f_subtrahend.close()
        description = "image_operate subtract (image subtraction):\n"
        description += (dset_minuend + "@" + str(args.minuend) + " -\n" +
                        dset_subtrahend + "@" + str(args.subtrahend))
        print("\n" + description + "\n")
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

    def multiply(self):
        """Multiply two images element-wise"""
        parser = argparse.ArgumentParser(description='Multiply many images, '
                                                     'element-wise')
        parser.add_argument('factors',
                            metavar='factors_hdf5_files_list',
                            type=str,
                            nargs='+', default=None,
                            help='input single images '
                                 'hdf5 files that will be multiplied')
        parser.add_argument('-o', '--output',
                    default='default',
                    metavar='output',
                    type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])
        image_list = args.factors
        f_handler = h5py.File(image_list[0], "r")
        img1, _ = extract_single_image_from_hdf5(f_handler)
        shape1 = np.shape(img1)
        result_image = np.ones(shape1)
        f_handler.close()
        description = "image multiplication:\n"
        for single_img_hdf5_file in args.factors:
            f_handler = h5py.File(single_img_hdf5_file, "r")
            img, dataset = extract_single_image_from_hdf5(f_handler)
            result_image = multiply_images(result_image, img)
            f_handler.close()
            description += dataset + "@" + str(single_img_hdf5_file)
            if single_img_hdf5_file is not args.factors[-1]:
                description += " * \n"
        print("\n" + description + "\n")
        if args.output == "default":
            for single_img_hdf5_file in args.factors:
                store_single_image_in_existing_hdf5(single_img_hdf5_file,
                                                    result_image,
                                                    description=description)
        else:
                store_single_image_in_new_hdf5(args.output,
                                               result_image,
                                               description=description)

    def divide(self):
        """Divide two images element-wise"""
        parser = argparse.ArgumentParser(description='Divide element-wise '
                                                     'a numerator image by '
                                                     'a denominator image ')
        parser.add_argument('numerator', metavar='image1', type=str,
                            help='numerator single image hdf5 file')
        parser.add_argument('denominator', metavar='image2', type=str,
                            help='denominator single image hdf5 file')
        parser.add_argument('-o', '--output',
                    default='default',
                    metavar='output',
                    type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])
        f_numerator = h5py.File(args.numerator, "r")
        numerator_img, dset_numerator = \
            extract_single_image_from_hdf5(f_numerator)
        f_denominator = h5py.File(args.denominator, "r")
        denominator_img, dset_denominator = \
            extract_single_image_from_hdf5(f_denominator)
        result_image = divide_images(numerator_img, denominator_img)
        f_numerator.close()
        f_denominator.close()
        description = "image_operate divide (image division):\n"
        description += (dset_numerator + "@" + str(args.numerator) + " /\n" +
                        dset_denominator + "@" + str(args.denominator))
        print("\n" + description + "\n")
        if args.output == "default":
            store_single_image_in_existing_hdf5(args.numerator,
                                                result_image,
                                                description=description)
            store_single_image_in_existing_hdf5(args.denominator,
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
                    default='default',
                    metavar='output',
                    type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])
        cte = args.constant
        h5_input_handler = h5py.File(args.image, "r")
        image, dset = extract_single_image_from_hdf5(h5_input_handler)
        description = 'image_operate add_constant:\n'
        description += (dset + "@" + str(args.image) + " + " +
                        str(args.constant))
        print("\n" + description + "\n")
        result_image = add_cte_to_image(image, cte)
        h5_input_handler.close()
        if args.output == "default":
            store_single_image_in_existing_hdf5(args.image,
                                                result_image,
                                                description=description)
        else:
            store_single_image_in_new_hdf5(args.output,
                                           result_image,
                                           description=description)

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
                    default='default',
                    metavar='output',
                    type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])
        cte = args.constant
        h5_input_handler = h5py.File(args.image, "r")
        image, dset = extract_single_image_from_hdf5(h5_input_handler)
        description = 'image_operate subtract_image_to_constant:\n'
        description += (str(args.constant) + " - " +
                        dset + "@" + str(args.image))
        print("\n" + description + "\n")
        result_image = subtract_image_to_cte(cte, image)
        h5_input_handler.close()
        if args.output == "default":
            store_single_image_in_existing_hdf5(args.image,
                                                result_image,
                                                description=description)
        else:
            store_single_image_in_new_hdf5(args.output,
                                           result_image,
                                           description=description)

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
                            default='default',
                            metavar='output',
                            type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])
        cte = float(args.constant)
        h5_input_handler = h5py.File(args.image, "r")
        image, dset = extract_single_image_from_hdf5(h5_input_handler)
        result_image = multiply_image_by_constant(image, cte)
        description = 'image_operate multiply_by_constant:\n'
        description += (dset + "@" + str(args.image) + " * " +
                        str(args.constant))
        print("\n" + description + "\n")
        h5_input_handler.close()
        if args.output == "default":
            store_single_image_in_existing_hdf5(args.image,
                                                result_image,
                                                description=description)
        else:
            store_single_image_in_new_hdf5(args.output,
                                           result_image,
                                           description=description)

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
                    default='default',
                    metavar='output',
                    type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])
        cte = float(args.constant)
        h5_input_handler = h5py.File(args.image, "r")
        image, dset = extract_single_image_from_hdf5(h5_input_handler)
        result_image = divide_image_by_constant(image, cte)
        description = 'image_operate divide_by_constant:\n'
        description += (dset + "@" + str(args.image) + " / " +
                        str(args.constant))
        print("\n" + description + "\n")
        h5_input_handler.close()
        if args.output == "default":
            store_single_image_in_existing_hdf5(args.image,
                                                result_image,
                                                description=description)
        else:
            store_single_image_in_new_hdf5(args.output,
                                           result_image,
                                           description=description)

    def normalize(self):
        """Divide an image by a constant"""

        # TODO: Allow as inputs, things

        parser = argparse.ArgumentParser(description='normalize BL09 image')
        parser.add_argument('image', metavar='image',
                            type=str, help='hdf5 file with image to be '
                                           'normalized')
        parser.add_argument('ff_images',
                            metavar='FF_hdf5_files_list',
                            type=str,
                            nargs='+', default=None,
                            help='hdf5 files containing the FF image')
        parser.add_argument('-o', '--output',
                            default='default',
                            metavar='output',
                            type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])

        normalized_img, description = normalize_bl09_image_by_avg_FF(
            args.image, args.ff_images)
        print("\n" + description + "\n")
        if args.output == "default":
            store_single_image_in_existing_hdf5(args.image,
                                                normalized_img,
                                                description=description)
        else:
            store_single_image_in_new_hdf5(args.output,
                                           normalized_img,
                                           description=description)

def main():
    ImageOperate()


if __name__ == '__main__':
    main()
