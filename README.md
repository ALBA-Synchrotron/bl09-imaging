
**txrm2nexus** is a file format converter from 'xrm' and 'txrm' formats into 
'hdf5' format.

Applications present on the package:
- txrm2nexus
- mosaic2nexus
- normalize
- autotxrm2nexus
- automosaic2nexus
- autonormalize

txrm2nexus is a file format converter which converts 'txrm' tomography 
projections (output of the TXM microscope at mistral), to NeXus standard 
files compliant with the NXtomo nexus definition. 

mosaic2nexus application converts the .xrm mosaics into hdf5. 

normalize script can be used to normalize tomography projections, 
spectroscopy images, and mosaic images. The normalization is done using 
FF images, accelerator currents, and exposure times.

Three scripts called autotxrm2nexus, automosaic2nexus and autonormalize, allow
to automate the procedures of conversion for many files. 

This software is used at BL09 of the ALBA-CELLS Synchrotron.


-----

*txrm2nexus is distributed under the terms of the 
GNU General Public License (or GPL).*




