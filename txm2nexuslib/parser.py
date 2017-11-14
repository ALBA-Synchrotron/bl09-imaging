#!/usr/bin/python

"""
(C) Copyright 2017 - ALBA CELLS - CTGENSOFT
Author Marc Rosanes
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
import copy
import pprint
from tinydb import TinyDB


class ParserTXMScript:

    def __init__(self):
        self.collected_files = []
        self.parameters = {}
        self.filename = None
        self.extension = None        
        self.date = None
        self.sample = "sample0"
        self.energy = -1
        self.angle = -1000
        self.zpz = -1
        self.FF = False
        self.repetition = 0
        self.first_repetition = True
        self.subfolder = None
        
    def reset_repetition(self):
        self.first_repetition = True
        self.repetition = 0    
    
    def parse_energy(self, line):
        # If a parameter is modified, the repetitions must be reset
        self.reset_repetition()
        word_list = line.split()
        self.energy = round(float(word_list[-1]), 1)
        self.parameters['energy'] = self.energy
                
    def parse_angle(self, line):
        # If a parameter is modified, the repetitions must be reset
        self.reset_repetition()
        word_list = line.split()
        self.angle = round(float(word_list[-1]), 1)
        self.parameters['angle'] = self.angle
        
    def parse_zpz(self, line):
        # If a parameter is modified, the repetitions must be reset
        self.reset_repetition()
        word_list = line.split()
        self.zpz = round(float(word_list[-1]), 1)
        self.parameters['zpz'] = self.zpz

    def parse_subfolder(self, line):
        """Subfolder where the raw data file should be located"""
        # The repetition must not be reset in this case
        word_list = line.split()
        self.subfolder = int(round(word_list[-1]))
        self.parameters['subfolder'] = self.subfolder
        
    def is_FF(self):
        if "_FF" in self.filename:
            # If a parameter is modified, the repetitions must be reset
            if not self.FF:
                self.reset_repetition()
            self.FF = True
            self.parameters['FF'] = self.FF
        else:
            # If a parameter is modified, the repetitions must be reset
            if self.FF:
                self.reset_repetition()
            self.FF = False
            self.parameters['FF'] = self.FF
        
    def parse_sample_and_date(self):
        try:
            date_str = self.filename.split('_')[0]
            new_date = int(date_str)
            # If a parameter is modified, the repetitions must be reset
            if new_date != self.date:
                self.first_repetition = True
            self.date = new_date
            if (len(date_str) == 4 or 
                len(date_str) == 6 or 
                len(date_str) == 8):
                self.parameters['date'] = self.date
                new_sample = self.filename.split('_')[1]
                # If a parameter is modified, the repetitions must be reset
                if new_sample != self.sample:
                    self.first_repetition = True
                self.sample = new_sample                    
            else:
                new_sample = self.filename.split('_')[0]
                # If a parameter is modified, the repetitions must be reset
                if new_sample != self.sample:
                    self.first_repetition = True
                self.sample = new_sample
        except:
            self.parameters.pop('date', None)
            self.sample = self.filename.split('_')[0]
        self.parameters['sample'] = self.sample
        
    def parse_extension(self):
        self.extension = os.path.splitext(self.filename)[1]
        self.parameters['extension'] = self.extension        
        
    def parse_collect(self, line):
        if not self.first_repetition:
            self.repetition += 1
        self.parameters['repetition'] = self.repetition

        word_list = line.split()
        self.filename = word_list[-1]
        self.parameters['filename'] = self.filename
        self.first_repetition = False
        
        self.is_FF()
        self.parse_extension()
        self.parse_sample_and_date()

        store_parameters = copy.deepcopy(self.parameters)
        self.collected_files.append(store_parameters)

    def parse_script(self, txm_txt_script):
        f = open(txm_txt_script, 'r')
        lines = f.readlines()
        for i, line in enumerate(lines):
            if "moveto energy" in line:
                self.parse_energy(line)
            if "moveto T" in line:
                self.parse_angle(line)
            if "moveto ZPz" in line:
                self.parse_zpz(line)
            if "moveto folder" in line:
                self.parse_subfolder
            if "collect" in line:
                self.parse_collect(line)    
        return self.collected_files
                

class FileIndexer(object):

    def __init__(self):
        self.parser = ParserTXMScript()
        self.db_file_index = None

    def fill_db(self, txm_script):
        self.db_file_index = TinyDB('index.json')
        self.db_file_index.purge()
        collected_images = self.parser.parse_script(txm_script)
        self.db_file_index.insert_multiple(collected_images)
        return self.db_file_index

    def close_db(self):
        self.db_file_index.close()


def main():

    parser = ParserTXMScript()
    collected_images = parser.parse_script("many.txt")
    pretty_printer = pprint.PrettyPrinter(indent=4)
    pretty_printer.pprint(collected_images)


if __name__ == "__main__":
    main()
