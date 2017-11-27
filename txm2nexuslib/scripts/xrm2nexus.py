#!/usr/bin/python

"""
(C) Copyright 2016-2017 ALBA-CELLS
Authors: Marc Rosanes, Carlos Falcon, Zbigniew Reszela, Carlos Pascual
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
import datetime
import argparse
from argparse import RawTextHelpFormatter
from txm2nexuslib.xrmnex import FilesOrganization, xrmNXtomo, xrmReader


def main():

    print("\n")
    print(datetime.datetime.today())
    print("\n")

    def str2bool(v):
        return v.lower() in ("yes", "true", "t", "1")

    description = 'Create raw data hdf5 files thanks to groups of xrm files.'
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=RawTextHelpFormatter)
    parser.register('type', 'bool', str2bool)

    parser.add_argument('input_txm_script', metavar='input TXM txt file',
                        type=str, help='TXM txt script used as index for the '
                                       'xrm image files')
    parser.add_argument('--output-dir', type=str, default="./out/",
                        help='Directory where the hdf5 files will be created.'
                             '\n(default: out)')
    parser.add_argument('--organize-by-repetitions', type='bool',
                        default='False',
                        help='- If True: Organize by ZPz positions\n'
                             '- If False: Organize by repetitions\n'
                             '(default: False)')
    parser.add_argument('--use-existing-db', type='bool', default='False',
                        help='- If True: Use exisiting file indexing DB\n'
                             '- If False: Recreate file indexing DB\n'
                             '(default: False)')
    # TODO: The default use-subfolders value shall be True, once subfolders...
    # TODO: ...link implemented in the beamline.
    parser.add_argument('--use-subfolders', type='bool', default='False',
                        help='- If True: Use subfolders for raw data\n'
                             '- If False: Go through the complete list of '
                             'folders/subfolders hang from the root folder\n'
                             '(default: False)')
    parser.add_argument('--title', type=str, default='X-ray tomography',
                        help="Sets the title of the tomography")
    parser.add_argument('--source-name', type=str, default='ALBA',
                        help="Sets the source name")
    parser.add_argument('--source-type', type=str,
                        default='Synchrotron X-ray Source',
                        help="Sets the source type")
    parser.add_argument('--source-probe', type=str, default='x-ray',
                        help="Sets the source probe. Possible options are:"
                             "'x-ray', 'neutron','electron'")
    parser.add_argument('--instrument-name', type=str, default='BL09 @ ALBA',
                        help="Sets the instrument name")

    args = parser.parse_args()

    txm_txt_script = args.input_txm_script
    output_dir = os.path.abspath(args.output_dir)
    files_dict = FilesOrganization()
    by_repetitions = args.organize_by_repetitions
    samples = files_dict.get_samples(txm_txt_script,
                                     use_existing_db=args.use_existing_db,
                                     use_subfolders=args.use_subfolders,
                                     organize_by_repetitions=by_repetitions)

    # Generate the hdf5 files
    for sample in samples.keys():
        tomos = samples[sample]['tomos']
        # Create FF reader
        ff_files = samples[sample]['ff']
        ffreader = xrmReader(ff_files)
        for tomo in tomos.keys():
            tomo_files = samples[sample]['tomos'][tomo]
            if len(ff_files) == 0:
                print "WARNING: %s of Sample: %s have not BrightField " \
                      "files." % (tomo, sample)
                continue
            reader = xrmReader(tomo_files)
            xrm = xrmNXtomo(reader, ffreader,
                            'sb',  # TODO: Not need?
                            'xrm2nexus',
                            hdf5_output_path=output_dir,
                            title=args.title,
                            zero_deg_in=None,  # TODO Not well implemented
                            zero_deg_final=None,  # TODO Not well implemented
                            sourcename=args.source_name,
                            sourcetype=args.source_type,
                            sourceprobe=args.source_probe,
                            instrument=args.instrument_name,
                            )
            xrm.convert_metadata()
            xrm.convert_tomography()

    print("\n")
    print(datetime.datetime.today())
    print("\n")


if __name__ == "__main__":
    main()

