dicom2stl
=========

[![CircleCI](https://circleci.com/gh/dave3d/dicom2stl.svg?style=svg)](https://circleci.com/gh/dave3d/dicom2stl)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/dave3d/dicom2stl/main?filepath=examples%2FIsosurface.ipynb)
![Python application](https://github.com/dave3d/dicom2stl/workflows/Python%20application/badge.svg)

Tutorial: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/dave3d/dicom2stl/main?filepath=examples%2FTutorial.ipynb)

dicom2stl.py is a script that takes a [Dicom](https://www.dicomstandard.org/about/)
series and generates a STL surface mesh.

Written by David T. Chen from the National Institute of Allergy & Infectious Diseases (NIAID),
dchen@mail.nih.gov It is covered by the Apache License, Version 2.0:
> http://www.apache.org/licenses/LICENSE-2.0

Getting Started
===============
The script is written in Python and uses 3 external packages, [SimpleITK](https://simpleitk.readthedocs.io/en/master/), [VTK](https://vtk.org), and [pydicom](https://pydicom.github.io/).

The dependencies can be installed using `pip`:
> pip install SimpleITK vtk pydicom

The options for the main script, **dicom2stl.py**, can be seen by running it:
> python dicom2stl.py --help


How dicom2stl.py works
======================
The script starts by reading in a series of 2-d images or a simple 3-d image.
It can read any format supported by ITK.  If the input name is a zip file or
a directory name, the script expects a single series of DCM images, all with
the ".dcm" suffix.

Note: if this script is run with the individual Dicom slices provided on the
command line, the slices might not be ordered in the correct order.  It is
better to provide a zip file or a directory, so ITK can determine the proper
slice ordering.  Dicom slices are not necessarily ordered the same
alphabetically as they are physically.  In the case of a zip file or directory,
the script loads using the
[SimpleITK ImageSeriesReader](https://simpleitk.readthedocs.io/en/master/Examples/DicomSeriesReader/Documentation.html)
class, which orders the slices by their physical layout, not their alphabetical
names.

The primary image processing pipeline is as follows:
* [Shrink](https://itk.org/SimpleITKDoxygen/html/classitk_1_1simple_1_1ShrinkImageFilter.html)
...the volume to 256 max dim (enabled by default)
* [Anisotropic smoothing](https://itk.org/SimpleITKDoxygen/html/classitk_1_1simple_1_1CurvatureAnisotropicDiffusionImageFilter.html)
...(disabled by default)
* [Double threshold filter](https://itk.org/SimpleITKDoxygen/html/classitk_1_1simple_1_1DoubleThresholdImageFilter.html)
...(enabled when tissue types are used)
* [Median filter](https://itk.org/SimpleITKDoxygen/html/classitk_1_1simple_1_1MedianImageFilter.html)
...(enabled for 'soft' and 'fat' tissue types)
* [Pad](https://itk.org/SimpleITKDoxygen/html/classitk_1_1simple_1_1ConstantPadImageFilter.html)
...the volume

The script has built in double threshold values for the 4 different tissue
types (bone, skin, muscle, soft).  These values assume the input is DICOM with
standard CT Hounsfield units.  I determined these values experimentally on a
few DICOM test sets, so the values might not work as well on other images.

The volume is shrunk to 256 cubed or less for speed and polygon count reasons.

After all the image processing is finished, the volume is converted to a VTK
image using sitk2vtk.py.

Then the following VTK pipeline is executed:
* [Extract a surface mesh](https://vtk.org/doc/nightly/html/classvtkContourFilter.html)
...from the VTK image
* Apply the [clean mesh filter](https://vtk.org/doc/nightly/html/classvtkCleanPolyData.html)
* [Remove small parts](https://vtk.org/doc/nightly/html/classvtkPolyDataConnectivityFilter.html)
...which connect to little other parts
* Apply the [smooth mesh filter](https://vtk.org/doc/nightly/html/classvtkSmoothPolyDataFilter.html)
* Apply the [reduce mesh filter](https://vtk.org/doc/nightly/html/classvtkQuadricDecimation.html)
* [Write out an STL file](https://vtk.org/doc/nightly/html/classvtkSTLWriter.html)

The amount of smoothing and mesh reduction can be adjusted via command line
options.  By default 25 iterations of smoothing is applied and the number of
vertices is reduced by 90%.


Examples
========

To extract the bone from a zip of dicom images:
> python dicom2stl.py -t bone -o bone.stl dicom.zip

To extract the skin from a NRRD volume:
> python dicom2stl.py -t skin -o skin.stl volume.nrrd

To extract a specific iso-value from a VTK volume:
> python dicom2stl.py -i 128 -o iso.stl volume.vtk

To extract soft tissue from a dicom series in directory and
apply a 180 degree Y axis rotation:
> python dicom2stl.py --enable rotation -t soft_tissue -o soft.stl dicom_dir

The options for the script can be seen by running it:
> python dicom2stl.py --help

You can try out an interactive Jupyter notebook via Binder:
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/dave3d/dicom2stl/main?filepath=examples%2FIsosurface.ipynb)
