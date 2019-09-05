[![Build Status](https://travis-ci.com/mrosanes/bl09-imaging.svg?branch=develop)](https://travis-ci.com/mrosanes/bl09-imaging)

 


bl09-imaging
------------


Image/Signal processing for BL09-Mistral Synchrotron Beamline Laboratory 
(formats: hdf5, mrc, xrm/txrm). 

It has been developed at ALBA Synchrotron Light Source. It is used for 
image processing purposes at BL09-Mistral Tomography and 2D-Spectroscopy 
Soft X-Ray Imaging Beamline.

A big part of the project involving the hdf5 image processing is generic, 
making it possible to be deployed and used in other Laboratories & Beamlines.


------


Some of the applications present on the package are:
- hdf2h5
- xrm2nexus
- txrm2nexus
- mosaic2nexus
- normalize
- autotxrm2nexus
- automosaic2nexus
- autonormalize

txrm2nexus is a file format converter which converts 'txrm' tomography 
projections (output of the TXM microscope at mistral), to hdf5 files.

mosaic2nexus application converts the .xrm mosaics into hdf5. 

normalize script can be used to normalize tomography projections, 
spectroscopy images, and mosaic images. The normalization is done using 
FF images, accelerator currents, and exposure times.

Three scripts called autotxrm2nexus, automosaic2nexus and autonormalize, allow 
to automate the procedures of conversion for many files.

bl09-imaging provides further applications and pipelines/workflows for 
tomography and other imaging techniques.


-----


*bl09-imaging (formerly txrm2nexus) is distributed under the terms of the 
GNU General Public License Version 3 (or GPLv3).*




