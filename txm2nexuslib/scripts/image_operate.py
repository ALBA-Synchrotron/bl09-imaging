#!/usr/bin/python

"""
(C) Copyright 2017-2018 ALBA-CELLS
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
            description='img allows performing operations with images stored'
                        'in hdf5 files',
            usage="""img <command> [<args>]

img commands:
   copy        - Copy hdf5 file to a new hdf5 file for processing
   clone       - Clone an hdf5 image dataset to a new dataset in the same file
   crop        - Crop image borders
   add         - Addition of many images
               - Add constant to image
   subtract    - From a reference image (minuend),
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
   align
               - Align image regarding another reference image
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
        copy_h5(args.input, output_fn)

    def crop(self):
        parser = argparse.ArgumentParser(
            description='Crop image borders',
            formatter_class=RawTextHelpFormatter)
        parser.add_argument('input_file', metavar='input_hdf5_filename',
                            type=str, help='input hdf5 filename containing '
                                           'the image to crop')
        parser.add_argument('-d', '--dataset',
                            type=str,
                            default="data",
                            help='Input dataset containing the image to crop')
        parser.add_argument('-t', '--top',
                            type=int,
                            default=26,
                            help='Top pixel rows to crop')
        parser.add_argument('-b', '--bottom',
                            type=int,
                            default=24,
                            help='Bottom pixel rows to crop')
        parser.add_argument('-l', '--left',
                            type=int,
                            default=21,
                            help='Left pixel columns to crop')
        parser.add_argument('-r', '--right',
                            type=int,
                            default=19,
                            help='Right pixel columns to crop')
        parser.add_argument('-s', '--store',
                            default='default',
                            metavar='True',
                            type=str, help='Store or not the resulting image')
        parser.add_argument('-o', '--output',
                            default='default',
                            type=str, help='output hdf5 filename')
        parser.add_argument('-nd', '--new-dataset',
                            default='data',
                            type=str, help='dataset name useful if storing'
                                           'in a freshly new hdf5')
        args = parser.parse_args(sys.argv[2:])

        roi = {"top": args.top, "bottom": args.bottom,
               "left": args.left, "right": args.right}
        image = Image(h5_image_filename=args.input_file,
                      image_data_set=args.dataset)

        image_cropped, description = image.crop(roi=roi)
        if args.store:
            if args.output == "default":
                image.store_image_in_h5(image_cropped,
                                        description=description)
            else:
                store_single_image_in_new_h5(
                    args.output, image_cropped, description=description,
                    data_set=args.new_dataset)
        image.close_h5()

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
        parser = argparse.ArgumentParser(
            description='Divide an hdf5 image or a constant (numerator), '
                        'by other hdf5 images or constants (denominators)\n'
                        'At least one term must be an hdf5 image',
            formatter_class=RawTextHelpFormatter)
        parser.add_argument('numerator', metavar='image1', type=str,
                            help='numerator single image hdf5 file')
        parser.add_argument('denominators', metavar='denominators',
                            type=str, nargs='+',
                            help='denominator single image hdf5 file(s) '
                                 'and/or constants')
        parser.add_argument('-o', '--output',
                    default='default',
                    metavar='output',
                    type=str, help='output hdf5 filename')
        args = parser.parse_args(sys.argv[2:])

        divide(args.numerator, args.denominators,
               store=True, output_h5_fn=args.output)

    def normalize(self):
        """
        Normalize BL09 hdf5 image: Normalize image by current, exposure time,
        and FF image (or FF average image), which at its turn have been
        normalized also by current and exposure time.
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

    def clone(self):
        """Clone an image to a new dataset"""
        parser = argparse.ArgumentParser(
            description='Clone an image located in a hdf5 file, to a new'
                        'dataset in the same file',
            formatter_class=RawTextHelpFormatter)
        parser.add_argument('input_file', type=str,
                            help='hdf5 input file containing the single '
                                 'image to be cloned')
        parser.add_argument('-d', '--dataset',
                            type=str,
                            default="data",
                            help='dataset containing the image to clone')
        args = parser.parse_args(sys.argv[2:])

        image = Image(h5_image_filename=args.input_file,
                      image_data_set=args.dataset)
        image.clone_image_dataset()

    def align(self):
        """Align a given image regarding another reference image"""
        parser = argparse.ArgumentParser(
            description='Align an image located in a hdf5 file, regarding'
                        'a reference image situated in another hdf5 file',
            formatter_class=RawTextHelpFormatter)
        parser.add_argument('input_file', type=str,
                            help='hdf5 input file containing the '
                                 'image to be aligned')
        parser.add_argument('reference_file', type=str,
                            help='hdf5 reference file containing the '
                                 'image used as reference')
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
        args = parser.parse_args(sys.argv[2:])

        image = Image(h5_image_filename=args.input_file,
                      image_data_set=args.dataset_for_aligning)
        reference_image_obj = Image(h5_image_filename=args.reference_file,
                                    image_data_set=args.dataset_reference)
        image.align_and_store(reference_image_obj, roi_size=args.roi_size)


def main():
    ImageOperate()


if __name__ == '__main__':
    main()
