
**txrm2nexus** is a file format converter from 'xrm' and 'txrm' formats into 
'hdf5' format.

Applications present on the package:
- hdf2h5
- xrm2nexus
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


TODO:

About building blocks image_operate:
Things that could be done:

- metadata h5 group for each image data set
  (data_1, data_2... -> metadata_1, metadata_2...).
- Names could be shorter (image_operate, multiply_by_constant, ...)
- metadata h5 group for each image data set (data_1, data_2... ->
                                             metadata_1, metadata_2...).
- Copy or link all metadata excepting the one that it has not anymore sense,
  or the one that has been modified between one data step and the next one.



-----

*txrm2nexus is distributed under the terms of the 
GNU General Public License (or GPL).*




