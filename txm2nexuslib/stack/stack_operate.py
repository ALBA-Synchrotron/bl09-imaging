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


import h5py
import numpy as np
from tinydb import TinyDB

try:
    import mrcfile
except Exception:
    msg = "mrcfile library is required to convert h5 files to mrc"
    raise msg


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
    mrc_stack_fn = h5_stack_fn.rsplit('.', 1)[0] + '.mrc'
    mrc_outfile = mrcfile.new_mmap(mrc_stack_fn,
                                   shape=(n_frames, n_rows, n_cols),
                                   mrc_mode=2,
                                   overwrite=True)

    # Convert the h5 images and store them in the freshly created mrc file
    for n_img in range(n_frames):
        mrc_outfile.data[n_img, :, :] = h5_group[dataset][n_img]
    mrc_outfile.flush()
    mrc_outfile.close()
    print("Stack {} has been converted to mrc".format(mrc_stack_fn))
    return mrc_stack_fn


def hdf5_2_mrc_stacks(db_filename, table_name="hdf5_stacks"):
    """Convert multiple hdf5 stack to mrc"""

    print("Converting multiple hdf5 stacks to mrc")
    db = TinyDB(db_filename)
    stack_table = db.table(table_name)
    mrc_stack_table = db.table("mrc_stacks")
    mrc_stack_table.purge()
    for record in stack_table.all():
        h5_stack_fn = record["filename"]
        print(h5_stack_fn)
        mrc_stack_fn = hdf5_2_mrc_stack(h5_stack_fn)
        record_mrc = record.copy()
        record_mrc["filename"] = mrc_stack_fn
        record_mrc["extension"] = ".mrc"
        mrc_stack_table.insert(record_mrc)
    print("")

    """
    import pprint
    pretty_printer = pprint.PrettyPrinter(indent=4)
    print("Created stacks:")
    for record in stack_table.all():
        pretty_printer.pprint(record["filename"])
        pretty_printer.pprint(record["extension"])
    for record in mrc_stack_table.all():
        pretty_printer.pprint(record["filename"])
        pretty_printer.pprint(record["extension"])
    """

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
    mrc_ln_stack_fn = mrc_stack_fn.rsplit('.', 1)[0] + '_ln.mrc'
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
    for record_mrc in mrc_stack_table.all():
        mrc_ln_stack_fn = minus_ln_stack_mrc(record_mrc["filename"])
        record_ln_mrc = record_mrc.copy()
        record_ln_mrc["filename"] = mrc_ln_stack_fn
        record_ln_mrc["extension"] = ".mrc"
        record_ln_mrc["absorbance"] = True
        mrc_stack_table.insert(record_ln_mrc)
    print("")

    """
    import pprint
    pretty_printer = pprint.PrettyPrinter(indent=4)
    print("Created stacks:")
    for record in mrc_stack_table.all():
        pretty_printer.pprint(record["filename"])
        pretty_printer.pprint(record["extension"])
        pretty_printer.pprint(record)
    """