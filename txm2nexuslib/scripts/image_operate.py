#!/usr/bin/python

"""
(C) Copyright 2014-2017 Marc Rosanes
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


import argparse
import sys


class ImageOperate(object):

    def __init__(self):
        parser = argparse.ArgumentParser(
            description='image_operate allows performing operations '
                        'with images',
            usage="""image_operate <command> [<args>]

The most commonly used image_operate commands are:
   sum           Sum of many images
   subtract      From a reference image, subtract another image
""")
        parser.add_argument('command', help='Subcommand to run')
        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print 'Unrecognized command'
            parser.print_help()
            exit(1)
        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def sum(self):
        parser = argparse.ArgumentParser(
            description='Sum of many images')
        parser.add_argument('-a', '--addends-list', action='append',
                            required=True,
                            metavar='[addends_hdf5_files_list]',
                            help='input the addends single image '
                                 'hdf5 files entered as a list')
        # prefixing the argument with -- means it's optional
        args = parser.parse_args(sys.argv[2:])
        print(args)
        print 'Running image_operate sum'

    def subtract(self):
        parser = argparse.ArgumentParser(
            description='From a reference image (minuend), '
                        'subtract another image (subtrahend)')
        # NOT prefixing the argument with -- means it's not optional
        parser.add_argument('minuend', metavar='minuend_hdf5_file',
                            type=str, help='reference single image hdf5 file')
        parser.add_argument('subtrahend', metavar='subtrahend_hdf5_file',
                            type=str, help='single image hdf5 file to subtract'
                                           'to the reference image')

        args = parser.parse_args(sys.argv[2:])
        print ('Running image_operate subtract: %s - %s' % (args.minuend,
                                                            args.subtrahend))


def main():
    ImageOperate()

if __name__ == '__main__':
    main()
