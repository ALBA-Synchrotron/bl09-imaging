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
    outfile_fn = h5_stack_fn.rsplit('.', 1)[0] + '.mrc'
    mrc_outfile = mrcfile.new_mmap(outfile_fn,
                                   shape=(n_frames, n_rows, n_cols),
                                   mrc_mode=2,
                                   overwrite=True)

    # Convert the h5 images and store them in the freshly created mrc file
    for n_img in range(n_frames):
        mrc_outfile.data[n_img, :, :] = h5_group[dataset][n_img]
    mrc_outfile.flush()
    mrc_outfile.close()


def hdf5_2_mrc_stacks(db_filename, table_name="hdf5_stacks"):
    """Convert multiple hdf5 stack to mrc"""

    print("Converting multiple hdf5 stacks to mrc")
    db = TinyDB(db_filename)
    stack_table = db.table(table_name)
    for record in stack_table.all():
        h5_stack_fn = record["filename"]
        hdf5_2_mrc_stack(h5_stack_fn)
