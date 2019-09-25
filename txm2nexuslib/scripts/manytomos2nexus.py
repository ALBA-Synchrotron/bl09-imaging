#!/usr/bin/python

"""
(C) Copyright 2016-2017 Carlos Falcon, Zbigniew Reszela, Marc Rosanes
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
from txm2nexuslib.xrmnex import xrmNXtomo, xrmReader


def get_samples(dir_name):
    samples = {}
    # Splits the files by samples
    for file in os.listdir(dir_name):
        fname = os.path.join(dir_name, file)
        if not os.path.isfile(fname) or fname.rsplit('.', 1)[1] != 'xrm':
            continue

        splitted_name = file.split('_')
        has_ff = file.find('_FF_') != -1

        sample_name = "{0}_{1}_{2}".format(splitted_name[0],
                                           splitted_name[1],
                                           splitted_name[2],
                                           )
        if not samples.has_key(sample_name):
            samples[sample_name] = {'tomos': {}, 'ff': []}
        if not has_ff:
            tomo_name = splitted_name[-1]
            if not samples[sample_name]['tomos'].has_key(tomo_name):
                samples[sample_name]['tomos'][tomo_name] = []
            samples[sample_name]['tomos'][tomo_name].append(fname)
        else:
            samples[sample_name]['ff'].append(fname)

    return samples


def main():

    print("\n")
    print(datetime.datetime.today())
    print("\n")

    description = 'Create a tomo hdf5 file per each group of existing xrm ' \
                  'files in the given directory'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('input_dir_name', metavar='input path', type=str,
                        help='Directory that has the Tomography, BrightField '
                        'and DarkField xrm files')
    parser.add_argument('--output-dir-name', type=str, default=None,
                        help='Directory where the hdf5 files will be created. '
                             'If it is not given the input dir will be used')
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

    dir_name = args.input_dir_name
    output_dir = args.output_dir_name
    samples = get_samples(dir_name)
    # Generate the hdf5 files
    for sample in samples.keys():
        tomos = samples[sample]['tomos']
        # Create FF reader
        ff_files = samples[sample]['ff']
        ff_files.sort(key=lambda x: os.path.getmtime(x))
        ffreader = xrmReader(ff_files)
        for tomo in tomos.keys():
            tomo_files = samples[sample]['tomos'][tomo]
            if len(ff_files) == 0:
                print "WARNING: %s of Sample: %s have not BrightField " \
                      "files. HDF5 file can not be created for this tomo" %\
                      (tomo, sample)
                continue
            # sort files
            tomo_files.sort(key=lambda x: os.path.getmtime(x))

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

