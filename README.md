dicom2stl
=========

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/dave3d/dicom2stl/main?filepath=examples%2FIsosurface.ipynb)
![Python application](https://github.com/dave3d/dicom2stl/workflows/Python%20application/badge.svg)

Tutorial: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/dave3d/dicom2stl/main?filepath=examples%2FTutorial.ipynb)

**dicom2stl** is a script that takes a [DICOM](https://www.dicomstandard.org/about/)
series and generates a STL surface mesh.

Written by David T. Chen from the National Institute of Allergy & Infectious Diseases (NIAID),
dchen@mail.nih.gov.  It is covered by the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

Getting Started
===============
The script is written in Python and uses 4 external packages, [SimpleITK](https://simpleitk.readthedocs.io/), [SimpleITKUtilities](https://github.com/SimpleITK/SimpleITKUtilities), [VTK](https://vtk.org), and [pydicom](https://pydicom.github.io/).

dicom2stl and its dependencies can be installed using pip:

```
    pip install dicom2stl
```

The options for the main script, **dicom2stl**, can be seen by running it:
```
    dicom2stl --help
```

Once you have a DICOM image series zip you can run your first script (Ensure that the \".zip\" file is in the dicom2stl directory):
```
    dicom2stl -t tissue -o output.stl dicom.zip
```

This will create a .stl file named \"output.stl\" that extracted tissue from the DICOM image series.

How dicom2stl works
======================
The script starts by reading in a series of 2-d images or a simple 3-d image.
It can read any
[image file format supported by SimpleITK](https://simpleitk.readthedocs.io/en/latest/IO.html).
If the input name is a zip file or
a directory name, the script expects a single series of DCM images, all with
the \".dcm\" suffix.

Note: if this script is run with the individual DICOM slices provided on the
command line, the slices might not be ordered in the correct order.  It is
better to provide a zip file or a directory, so ITK can determine the proper
slice ordering.  DICOM slices are not necessarily ordered the same
alphabetically as they are physically.  In the case of a zip file or directory,
the script loads using the
[SimpleITK ImageSeriesReader](https://simpleitk.readthedocs.io/en/master/link_DicomSeriesReader_docs.html)
class, which orders the slices by their physical layout, not their alphabetical
names.

The primary image processing pipeline is as follows:

 * [Shrink](https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ShrinkImageFilter.html)
   the volume to 256 max dim (enabled by default)
 * [Anisotropic smoothing](https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1CurvatureAnisotropicDiffusionImageFilter.html)
   (disabled by default)
 * [Double threshold filter](https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1DoubleThresholdImageFilter.html)
   (enabled when tissue types are used)
 * [Median filter](https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1MedianImageFilter.html)
   (enabled for \'soft\' and \'fat\' tissue types)
 * [Pad](https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ConstantPadImageFilter.html)
   the volume

The script has built in double threshold values for the 4 different tissue
types (bone, skin, muscle, soft).  These values assume the input is DICOM with
standard CT Hounsfield units.  I determined these values experimentally on a
few DICOM test sets, so the values might not work as well on other images.

The volume is shrunk to 256 cubed or less for speed and polygon count reasons.

After all the image processing is finished, the volume is converted to a VTK
image using sitk2vtk from SimpleITKUtilities.

Then the following VTK pipeline is executed:

 * [Extract a surface mesh](https://vtk.org/doc/nightly/html/classvtkContourFilter.html)
   from the VTK image
 * Apply the [clean mesh filter](https://vtk.org/doc/nightly/html/classvtkCleanPolyData.html)
 * [Remove small parts](https://vtk.org/doc/nightly/html/classvtkPolyDataConnectivityFilter.html)
   which connect to little other parts
 * Apply the [smooth mesh filter](https://vtk.org/doc/nightly/html/classvtkSmoothPolyDataFilter.html)
 * Apply the [reduce mesh filter](https://vtk.org/doc/nightly/html/classvtkQuadricDecimation.html)
 * [Write out an STL file](https://vtk.org/doc/nightly/html/classvtkSTLWriter.html)

The amount of smoothing and mesh reduction can be adjusted via command line
options.  By default 25 iterations of smoothing are applied and the number of
vertices is reduced by 90%.

Basic Usage & Options
========
```
usage: dicom2stl [-h] [--verbose] [--debug] [--output OUTPUT] [--meta META] [--ct] [--clean] [--temp TEMP] [--search SEARCH]
                    [--type {skin,bone,soft_tissue,fat}] [--anisotropic] [--isovalue ISOVALUE] [--double DOUBLE_THRESHOLD] [--largest]
                    [--rotaxis {X,Y,Z}] [--rotangle ROTANGLE] [--smooth SMOOTH] [--reduce REDUCE] [--clean-small SMALL]
                    [--enable {anisotropic,shrink,median,largest,rotation}] [--disable {anisotropic,shrink,median,largest,rotation}]
                    [filenames ...]
```
For a definitive list of options, run:
```
    dicom2stl --help
```


Examples
========

To extract the type \"bone\" from a zip of dicom images to an output file \"bone.stl\":
```
    dicom2stl -t bone -o bone.stl dicom.zip
```

To extract the skin from a NRRD volume:
```
    dicom2stl -t skin -o skin.stl volume.nrrd
```

To extract a specific iso-value (128) from a VTK volume:
```
    dicom2stl -i 128 -o iso.stl volume.vtk
```

To extract soft tissue from a DICOM series in directory and
apply a 180 degree Y axis rotation:
```
    dicom2stl --enable rotation -t soft_tissue -o soft.stl dicom_dir
```

The options for the script can be seen by running it:
```
    dicom2stl --help
```

You can try out an interactive Jupyter notebook via Binder:
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/dave3d/dicom2stl/main?filepath=examples%2FIsosurface.ipynb)
