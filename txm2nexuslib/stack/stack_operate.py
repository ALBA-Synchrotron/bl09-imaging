#!/usr/bin/python

"""
(C) Copyright 2019 ALBA-CELLS
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
import h5py
import subprocess
import numpy as np
from tinydb import TinyDB, Query

try:
    import mrcfile
except Exception:
    msg = "mrcfile library is required to convert h5 files to mrc"
    raise Exception(msg)


def hdf5_2_mrc_stack(h5_stack_fn,
                     tree="TomoNormalized", dataset="TomoNormalized"):
    """Convert a single hdf5 stack to mrc"""

    h5_handler = h5py.File(h5_stack_fn, "r")
    h5_group = h5_handler[tree]

    # Shape information of data image stack
    infoshape = h5_group[dataset].shape
    n_frames = infoshape[0]
    n_rows = infoshape[1]
    n_cols = infoshape[2]

    # Create empty mrc file
    mrc_stack_fn = os.path.splitext(h5_stack_fn)[0] + '.mrc'
    mrc_outfile = mrcfile.new_mmap(mrc_stack_fn,
                                   shape=(n_frames, n_rows, n_cols),
                                   mrc_mode=2,
                                   overwrite=True)

    # Convert the h5 images and store them in the freshly created mrc file
    for n_img in range(n_frames):
        mrc_outfile.data[n_img, :, :] = h5_group[dataset][n_img]

    angles_fn = None
    if (tree + "/rotation_angle") in h5_handler:
        angles_fn = "angles_" + os.path.splitext(h5_stack_fn)[0] + '.tlt'
        with open(angles_fn, "w") as angles_file:
            for angle in h5_group["rotation_angle"].value:
                angles_file.write("%.2f\n" % angle)

    mrc_outfile.flush()
    mrc_outfile.close()
    print("Stack {} has been converted to mrc".format(h5_stack_fn))
    return mrc_stack_fn, angles_fn


def hdf5_2_mrc_stacks(db_filename, table_name="hdf5_stacks"):
    """Convert multiple hdf5 stack to mrc"""

    print("Converting multiple hdf5 stacks to mrc")
    db = TinyDB(db_filename)
    stack_table = db.table(table_name)
    mrc_stack_table = db.table("mrc_stacks")
    mrc_stack_table.purge()
    for record in stack_table.all():
        h5_stack_fn = record["filename"]
        mrc_stack_fn, angles_fn = hdf5_2_mrc_stack(h5_stack_fn)
        record_mrc = record.copy()
        record_mrc["filename"] = mrc_stack_fn
        record_mrc["extension"] = ".mrc"
        # former_hdf5_fn is the filename of the first normalized stack hdf5
        record_mrc["former_hdf5_fn"] = h5_stack_fn
        if angles_fn:
            record_mrc["angles"] = angles_fn
        mrc_stack_table.insert(record_mrc)
    print("")
    db.close()


def deconvolve_stack(stack_fn):
    """Deconvolve an mrc stack"""
    pass


def minus_ln_stack_mrc(mrc_stack_fn):
    """Compute absorbance stack: Apply minus logarithm to a mrc stack"""

    mrc_handler = mrcfile.open(mrc_stack_fn, mode='r')

    infoshape = mrc_handler.data.shape
    n_frames = infoshape[0]
    n_rows = infoshape[1]
    n_cols = infoshape[2]

    # Create empty mrc file
    mrc_ln_stack_fn = os.path.splitext(mrc_stack_fn)[0] + '_ln.mrc'
    mrc_outfile = mrcfile.new_mmap(mrc_ln_stack_fn,
                                   shape=(n_frames, n_rows, n_cols),
                                   mrc_mode=2,
                                   overwrite=True)

    # Calculate absorbance (minus logarithm) stack and store on mrc
    for n_img in range(n_frames):
        img = mrc_handler.data[n_img, :, :]
        mrc_outfile.data[n_img, :, :] = -np.log(img)
    mrc_outfile.flush()
    mrc_outfile.close()

    print("Minus logarithm applied on stack {}".format(mrc_stack_fn))
    return mrc_ln_stack_fn


def minus_ln_stacks_mrc(db_filename, table_name="mrc_stacks"):
    """Compute absorbance stacks (by applying the minus natural logarithm)
    to multiple mrc stacks.
    """

    print("Compute absorbance stacks by applying the minus natural logarithm:")
    db = TinyDB(db_filename)
    mrc_stack_table = db.table(table_name)

    query = Query()
    mrc_stacks = mrc_stack_table.search(query.extension == ".mrc")
    for record_mrc in mrc_stacks:
        mrc_ln_stack_fn = minus_ln_stack_mrc(record_mrc["filename"])
        record_ln_mrc = record_mrc.copy()
        record_ln_mrc["filename"] = mrc_ln_stack_fn
        record_ln_mrc["extension"] = ".mrc"
        record_ln_mrc["absorbance"] = True
        record_ln_mrc["former_hdf5_fn"] = record_mrc["former_hdf5_fn"]
        mrc_stack_table.insert(record_ln_mrc)
    print("")


def align_ctalignxcorr(mrc_norm_stack_fn, hdf5_norm_stack=None):
    """"Automatic alignment using fiducials
    Usage of ctalignxcorr for aligning using fiducials"""

    align_command = "ctalignxcorr " + mrc_norm_stack_fn + " " + hdf5_norm_stack
    subprocess.call(align_command, shell=True)
    mrc_aligned_stack_old_fn = os.path.splitext(mrc_norm_stack_fn)[0] + '.ali'
    mrc_aligned_stack_fn = os.path.splitext(mrc_norm_stack_fn)[0] + '_ali.mrc'
    os.rename(mrc_aligned_stack_old_fn, mrc_aligned_stack_fn)
    return mrc_aligned_stack_fn


def align_ctalign(mrc_norm_stack_fn):
    """"Automatic alignment using ctalign:
    typically used for aligning without fiducials.
    ctalign requires an hdf5 file as input"""

    mrc2hdf_command = "mrc2hdf " + mrc_norm_stack_fn
    subprocess.call(mrc2hdf_command, shell=True)

    hdf5_norm_stack_fn = os.path.splitext(mrc_norm_stack_fn)[0] + '.hdf5'
    align_command = "ctalign " + hdf5_norm_stack_fn
    subprocess.call(align_command, shell=True)

    # Conversion back to a mrc file
    hdf5_ali_stack_fn = os.path.splitext(mrc_norm_stack_fn)[0] + '_ali.hdf5'
    mrc_aligned_stack_fn, angles_fn = hdf5_2_mrc_stack(
        hdf5_ali_stack_fn, tree="FastAligned", dataset="tomo_aligned")
    return mrc_aligned_stack_fn


def norm2ali_stack(record_to_align, mrc_stack_table=None,
                   absorbance=True, fiducials=False):
    """Align different projections of the same tomography stack"""

    mrc_stack_to_align_fn = record_to_align["filename"]
    print("Aligning stack: {0}".format(mrc_stack_to_align_fn))

    if fiducials:
        # Alignment using fiducials (execute ctalignxcorr which uses IMOD)
        print("ctalignxcorr: typically used for alignment with fiducials")
        hdf5_norm_stack = record_to_align["former_hdf5_fn"]
        mrc_aligned_stack = align_ctalignxcorr(mrc_stack_to_align_fn,
                                               hdf5_norm_stack)
    else:
        # Alignment without requiring fiducials
        print("ctalign: typically used for alignment without fiducials")
        mrc_aligned_stack = align_ctalign(mrc_stack_to_align_fn)

    if mrc_stack_table:
        record_aligned_mrc = record_to_align.copy()
        record_aligned_mrc["filename"] = mrc_aligned_stack
        record_aligned_mrc["absorbance"] = absorbance
        record_aligned_mrc["aligned"] = True
        mrc_stack_table.insert(record_aligned_mrc)

    return mrc_aligned_stack


def norm2ali_stacks(db_filename, table_name="mrc_stacks",
                    absorbance=True, fiducials=False):
    """Align all the projections of a stack, for multiple stacks"""

    print("Aligning all the projections of a stack, for multiple stacks:")
    db = TinyDB(db_filename)
    mrc_stack_table = db.table(table_name)

    query = Query()
    mrc_stacks_to_recons = mrc_stack_table.search(query.absorbance == True)
    if not mrc_stacks_to_recons:
        mrc_stacks_to_recons = mrc_stack_table.all()

    print("")
    for mrc_stack_to_ali_record in mrc_stacks_to_recons:
        mrc_aligned_stack = norm2ali_stack(
            mrc_stack_to_ali_record, mrc_stack_table,
            absorbance, fiducials)
        print("Aligned stack: %s" % mrc_aligned_stack)


def get_stacks_to_recons(db_filename, table_name="mrc_stacks",
                         align=False):
    """Get records of stacks in TinyDB that shall be reconstructed"""

    db = TinyDB(db_filename)
    mrc_stack_table = db.table(table_name)
    stack_query = Query()
    if align:
        stack_query_cmd = ((stack_query.absorbance == True)
                           & (stack_query.aligned == True))
        mrc_stacks_to_recons_records = mrc_stack_table.search(stack_query_cmd)
    else:
        stack_query_cmd = (stack_query.absorbance == True)
        mrc_stacks_to_recons_records = mrc_stack_table.search(stack_query_cmd)
        if not mrc_stacks_to_recons_records:
            mrc_stacks_to_recons_records = mrc_stack_table.all()

    return mrc_stacks_to_recons_records


def recons_mrc_stack(mrc_stack_to_recons_record, iterations=30):
    """Reconstruction and trim using tomo3d and IMOD trimvol"""

    mrc_stack_fn = mrc_stack_to_recons_record["filename"]
    mrc_stack_fn_xzy = os.path.splitext(mrc_stack_fn)[0] + '_recons.xzy'
    tilt_angles_fn = mrc_stack_to_recons_record["angles"]
    tomo3d_cmd = (
            "tomo3d -v 1 -l " + str(iterations) + " -z 500 -S -a " +
            tilt_angles_fn + " -i " + mrc_stack_fn +
            " -o " + mrc_stack_fn_xzy)
    subprocess.call(tomo3d_cmd, shell=True)

    # trim volume by rotating it
    mrc_recons_stack_fn = os.path.splitext(mrc_stack_fn_xzy)[0] + '.mrc'
    trim_cmd = ("trimvol -yz " + mrc_stack_fn_xzy + " " + mrc_recons_stack_fn)
    subprocess.call(trim_cmd, shell=True)

    return mrc_recons_stack_fn


def recons_mrc_stacks(mrc_stacks_to_recons_records, iterations=30):
    """Compute the reconstructed tomographies for
    multiple projection stacks"""

    print("Compute the reconstructed tomographies for "
          "multiple projection stacks:\n")
    for mrc_stack_to_recons_record in mrc_stacks_to_recons_records:
        recons_stack = recons_mrc_stack(mrc_stack_to_recons_record,
                                        iterations)
        print("Reconstructed stack: %s" % recons_stack)

    """
    import pprint
    pretty_printer = pprint.PrettyPrinter(indent=4)
    print("Created stacks:")
    for record in mrc_stack_table.search(stacks_to_recons_query.aligned == True):
        pretty_printer.pprint(record["filename"])
        pretty_printer.pprint(record["extension"])
        pretty_printer.pprint(record["aligned"])
        pretty_printer.pprint(record)
    """
