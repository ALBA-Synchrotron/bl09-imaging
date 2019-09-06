#!/usr/bin/python

"""
(C) Copyright 2018 ALBA-CELLS
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
import time
import subprocess
import argparse
from argparse import RawTextHelpFormatter
from tinydb import TinyDB, Query
from tinydb.middlewares import CachingMiddleware

from txm2nexuslib.parser import create_db, get_db_path
from txm2nexuslib.images.multiplexrm2h5 import multiple_xrm_2_hdf5
from txm2nexuslib.images.util import (
    copy2proc_multiple, check_if_multiple_zps, query_command_for_same_sample)
from txm2nexuslib.images.multiplecrop import crop_images
from txm2nexuslib.images.multiplenormalization import normalize_images
from txm2nexuslib.images.multiplealign import align_images
from txm2nexuslib.images.multipleaverage import average_image_groups
from txm2nexuslib.images.imagestostack import many_images_to_h5_stack
from txm2nexuslib.stack.stack_operate import (
    hdf5_2_mrc_stacks, deconvolve_stacks, minus_ln_stacks_mrc,
    norm2ali_stacks, get_stacks_to_recons, recons_mrc_stacks)


def main():
    """
    - Convert from xrm to hdf5 individual image hdf5 files
    - Copy raw hdf5 to new files for processing
    - Crop borders of single hdf5 image files
    - Normalize single hdf5 image files
    - Option: Create intermediate stacks by date, sample, energy and zpz,
      with multiple angles in each stack
    - Align multiple focus hdf5 single image files (same angle, different ZPz)
    - Average multiple hdf5 single image files (same angle, different ZPz)
    - Create stacks by date, sample and energy
      with multiple angles in each stack
    - Convert the stacks to mrc (optional)
    - Deconvolution of the stacks (optional)
    - Compute the absorbance stacks (apply the minus natural logarithm)
    - Align tomo projections of the same stack at different angles
    - Reconstruct tomographies using 3D tomo
    - Trim volume (volume reorientation) using IMOD trimvol
    """
    def str2bool(v):
        return v.lower() in ("yes", "true", "t", "1")

    description = ("Pre-Processing for BL09 Tomographies:\n" +
                   "From single xrm image files to reconstructed "
                   " tomographies.\nUsed for single tomographies and"
                   " for multifocal tomographies")

    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=RawTextHelpFormatter)
    parser.register('type', 'bool', str2bool)

    parser.add_argument('txm_txt_script', type=str,
                        help=('TXM txt script containing the commands used ' +
                              'to perform\nthe image acquisition by the ' +
                              'BL09 TXM microscope'))

    parser.add_argument('--crop', type='bool',
                        default='True',
                        help='- If True: Crop images\n'
                             '- If False: Do not crop images\n'
                             '(default: True)')

    parser.add_argument('--table_for_stack', type=str,
                        default='hdf5_averages',
                        help=("DB table of image files to create the stacks" +
                              "\n(default: hdf5_averages)"))

    parser.add_argument('-z', '--stacks_zp', type='bool',
                        default='True',
                        help="Store individual ZPz stacks (before"
                             " storage of multifocal FS stacks)\n"
                             "(default: True)")

    parser.add_argument('-m', '--hdf_to_mrc', type='bool',
                        default='True',
                        help="Convert FS hdf5 to mrc\n"
                             + "(default: True)")

    parser.add_argument('-d', '--deconvolution', type='bool',
                        default='False',
                        help="Deconvolve mrc normalized stacks\n"
                             + "(default: False)")

    parser.add_argument('-zp', '--zp-size', type=int,
                        default=25,
                        help="ZP zones size (in nm)\n"
                             + "(default: 25)")

    parser.add_argument('-t', '--thickness', type=int,
                        default=20,
                        help="Sample thickness (in um)\n"
                             + "(default: 20)")

    parser.add_argument('-l', '--minus_ln', type='bool',
                        default='False',
                        help="Compute absorbance stack [-ln(mrc)]\n"
                             + "(default: False)")

    parser.add_argument('-a', '--align', type='bool',
                        default='False',
                        help="Align the different tomography projections\n"
                             + "(default: False)")

    parser.add_argument('-f', '--fiducials', type='bool',
                        default='False',
                        help="Align using ctalign: -f=False"
                             " (typically used for non-fiducial alignment)\n"
                             + "Align using ctalignxcorr: -f=True"
                               " (typically used for fiducial alignment)\n"
                             + "(default: False)")

    parser.add_argument('-r', '--reconstruction', type='bool',
                        default='False',
                        help="Compute reconstructed tomography\n"
                             + "(default: False)")

    parser.add_argument('-i', '--iterations', type=int, default=30,
                        help='Iterations for tomo3d \n'
                             '(default=30)')

    args = parser.parse_args()

    print("\nPre-Processing for BL09 Tomographies:\n" +
          "-> xrm raw -> hdf5 raw -> hdf5 for processing -> crop ->\n" +
          "-> normalize -> align for same angle and variable zpz ->\n" +
          "-> average all images with same angle ->" +
          " make stacks -> hdf5 to mrc ->\n-> deconvolve -> apply minus" +
          " logarithm to compute the abosrbance stacks ->\n-> align the" +
          " projections at different angles -> reconstruct ->\n->" +
          " reorientate the volumes with trim")

    start_time = time.time()

    db_filename = get_db_path(args.txm_txt_script)
    create_db(args.txm_txt_script)
    # Multiple xrm 2 hdf5 files: working with many single images files
    multiple_xrm_2_hdf5(db_filename)

    # Copy of multiple hdf5 raw data files to files for processing
    copy2proc_multiple(db_filename)

    # Multiple files hdf5 images crop: working with single images files
    if args.crop:
        crop_images(db_filename)

    # Normalize multiple hdf5 files: working with many single images files
    normalize_images(db_filename)

    tomo_projections_query = query_command_for_same_sample(db_filename)
    single_zp_bool = check_if_multiple_zps(db_filename,
                                           query=tomo_projections_query)

    # Compute single stacks or intermediate stacks (each one for a ZPz)
    if single_zp_bool or args.stacks_zp:
        many_images_to_h5_stack(db_filename, table_name="hdf5_proc",
                                type_struct="normalized", suffix="_stack")

    # If many ZPz positions are used:
    if not single_zp_bool:
        # Align multiple hdf5 files: working with many single images files
        align_images(db_filename, align_method='cv2.TM_SQDIFF_NORMED')

        # Average multiple hdf5 files: working with many single images files
        average_image_groups(db_filename)

        # Build up hdf5 stacks from individual images
        many_images_to_h5_stack(db_filename, table_name="hdf5_proc",
                                type_struct="normalized_multifocus",
                                suffix="_FS")

    if args.hdf_to_mrc or args.deconvolution:

        if args.hdf_to_mrc and not args.deconvolution:
            # Convert FS stacks from hdf5 to mrc
            hdf5_2_mrc_stacks(db_filename)
        elif args.deconvolution:
            # Deconvolve the normalized stacks
            deconvolve_stacks(db_filename, zp_size=args.zp_size,
                              thickness=args.thickness)

        # Compute absorbance stacks
        if args.minus_ln:
            minus_ln_stacks_mrc(db_filename, deconvolution=args.deconvolution)

        # Align projections
        if args.align:
            norm2ali_stacks(db_filename, table_name="mrc_stacks",
                            deconvolution=args.deconvolution,
                            absorbance=args.minus_ln,
                            fiducials=args.fiducials)

        # Compute the reconstructed stacks
        if args.reconstruction:
            mrc_stacks_to_recons_records = get_stacks_to_recons(
                db_filename, table_name="mrc_stacks",
                deconvolution=args.deconvolution, absorbance=args.minus_ln,
                align=args.align)
            recons_mrc_stacks(mrc_stacks_to_recons_records,
                              iterations=args.iterations)

    print("\nExecution took %d seconds\n" % (time.time() - start_time))


if __name__ == "__main__":
    main()
