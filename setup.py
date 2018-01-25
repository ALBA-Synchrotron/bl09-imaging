#!/usr/bin/env python

from setuptools import setup, find_packages

# txrm2nexus setup.py for usage of setuptools

# The version is updated automatically with bumpversion
# Do not update manually
__version = '10.15.0-alpha'

long_description = """This project allows to process in many ways images in
hdf5 format. Moreover it allows to convert from xrm/txrm formats into
hdf5 format. It has been developd at ALBA Synchrotron Light Source, and
it is mainly used for image processing purposes at BL09-Mistral Beamline.
"""

classifiers = [
    # How mature is this project? Common values are
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    'Development Status :: 3 - Alpha',

    # Indicate who your project is intended for
    'Intended Audience :: Science/Research',
    'Topic :: Scientific/Engineering',
    'Topic :: Software Development :: Libraries',

    # Pick your license as you wish (should match "license" above)
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    'Programming Language :: Python :: 2.7',
]


setup(
    name='txrm2nexus',
    version=__version,
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'xrm2h5 = txm2nexuslib.scripts.xrm2h5:main',
            'xrm2nexus = txm2nexuslib.scripts.xrm2nexus:main',
            'manytomos2nexus = txm2nexuslib.scripts.manytomos2nexus:main',
            'txrm2nexus = txm2nexuslib.scripts.txrm2nexus:main',
            'mosaic2nexus = txm2nexuslib.scripts.mosaic2nexus:main',
            'normalize = txm2nexuslib.scripts.normalize:main',
            'magnify = txm2nexuslib.scripts.magnify:main',
            'autotxrm2nexus = txm2nexuslib.scripts.autotxrm2nexus:main',
            'automosaic2nexus = txm2nexuslib.scripts.automosaic2nexus:main',
            'autonormalize = txm2nexuslib.scripts.autonormalize:main',
            'img = txm2nexuslib.scripts.image_operate:main',
            'copy2proc = txm2nexuslib.scripts.copy2proc:main',
            'manyxrm2h5 = txm2nexuslib.scripts.manyxrm2h5:main',
            'manynorm = txm2nexuslib.scripts.manynorm:main',
            'manycrop = txm2nexuslib.scripts.manycrop:main',
            'manyalign = txm2nexuslib.scripts.manyalign:main',
            'manyaverage = txm2nexuslib.scripts.manyaverage:main',
            'img2stack = txm2nexuslib.scripts.img2stack:main',
            'manyxrm2norm = txm2nexuslib.workflows.manyxrm2norm:main',
            'xtendof = txm2nexuslib.workflows.xtendof:main']
    },
    author='Marc Rosanes, Carlos Falcon, Zbigniew Reszela, Carlos Pascual',
    author_email='mrosanes@cells.es, cfalcon@cells.es, zreszela@cells.es, '
                 'cpascual@cells.es',
    maintainer='ctgensoft',
    maintainer_email='ctgensoft@cells.es',
    url='https://git.cells.es/controls/txrm2nexus',
    keywords='APP',
    license='GPLv3',
    description='HDF5 images pre-processing (formats: hdf5, xrm, txrm)',
    long_description=long_description,
    requires=['setuptools (>=1.1)'],
    install_requires=['numpy'],
    classifiers=classifiers
)

