dicom2stl
=========

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/dave3d/dicom2stl/main?filepath=examples%2FIsosurface.ipynb)
![Python application](https://github.com/dave3d/dicom2stl/workflows/Python%20application/badge.svg)

Tutorial: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/dave3d/dicom2stl/main?filepath=examples%2FTutorial.ipynb)

**dicom2stl** is a script that takes a [DICOM](https://www.dicomstandard.org/about/) series and generates an [STL surface mesh](https://en.wikipedia.org/wiki/STL_(file_format)).

**Use cases:** Medical visualization, 3D printing anatomical models, creating patient-specific implants, surgical planning, and research.

Written by David T. Chen from the National Institute of Allergy & Infectious Diseases (NIAID), dchen@mail.nih.gov. It is covered by the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

Prerequisites
=============

- **Python 3.7 or higher**
- Compatible with Linux, macOS, and Windows

The script uses 4 external packages:
- [SimpleITK](https://simpleitk.readthedocs.io/) - Medical image processing
- [SimpleITKUtilities](https://github.com/SimpleITK/SimpleITKUtilities) - Conversion utilities
- [VTK](https://vtk.org) - 3D visualization and mesh processing (version 9+ recommended)
- [pydicom](https://pydicom.github.io/) - DICOM file parsing

Getting Started
===============

**Installation:**

```bash
pip install dicom2stl
```

**Quick Start:**

```bash
# Extract bone tissue from a DICOM zip file
dicom2stl -t bone -o bone.stl dicom.zip

# Extract from a directory of DICOM files
dicom2stl -t skin -o skin.stl /path/to/dicom/directory

# See all available options
dicom2stl --help
```

How dicom2stl works
======================
The script starts by reading in a series of 2-d images or a simple 3-d image.
It can read any
[image file format supported by SimpleITK](https://simpleitk.readthedocs.io/en/latest/IO.html).
If the input name is a zip file or
a directory name, the script expects a single series of DCM images, all with
the \".dcm\" suffix.

**Important:** When processing DICOM files, always use a zip file or directory rather than listing individual files on the command line. DICOM slices are not necessarily ordered alphabetically the same as they are physically. When given a zip file or directory, the script uses [SimpleITK's ImageSeriesReader](https://simpleitk.readthedocs.io/en/master/link_DicomSeriesReader_docs.html) which correctly orders slices by their physical layout using DICOM metadata.

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

The script has built-in double threshold values for 4 different tissue types:

- **bone** - Hard tissue (200-800, 1300-1500 HU)
- **skin** - Soft outer tissue (-200-0, 500-1500 HU)  
- **soft** - Soft tissue/muscle (-15-30, 58-100 HU)
- **fat** - Adipose tissue (-122 to -112, -96 to -70 HU)

These values assume the input is DICOM with standard CT Hounsfield units. They were determined experimentally on several DICOM test sets, so results may vary on other images.

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

Command-Line Options
====================

**Key Options:**

- `-t, --type {bone,skin,soft,fat}` - Tissue type to extract
- `-o, --output` - Output STL file path
- `-i, --isovalue` - Iso-surface value (for non-tissue extraction)
- `--double` - Custom double threshold values (format: "t1;t2;t3;t4")
- `--smooth N` - Number of smoothing iterations (default: 25)
- `--reduce N` - Mesh reduction factor, 0-1 (default: 0.9)
- `--rotaxis {X,Y,Z}` - Rotation axis
- `--rotangle` - Rotation angle in degrees
- `--enable/--disable {shrink,anisotropic,median,largest,rotation}` - Enable/disable filters
- `--verbose` - Verbose output
- `--debug` - Debug mode with detailed information

For complete options, run:
```bash
dicom2stl --help
```


Examples
========

**Basic tissue extraction:**

```bash
# Extract bone from DICOM zip file
dicom2stl -t bone -o bone.stl dicom.zip

# Extract skin from directory
dicom2stl -t skin -o skin.stl /path/to/dicom/folder

# Extract soft tissue
dicom2stl -t soft -o soft.stl dicom.zip
```

**Non-DICOM formats:**

```bash
# Extract from NRRD volume
dicom2stl -t skin -o skin.stl volume.nrrd

# Extract specific iso-value from VTK volume
dicom2stl -i 128 -o iso.stl volume.vtk
```

**Advanced options:**

```bash
# Apply rotation during processing
dicom2stl --enable rotation --rotaxis Y --rotangle 180 -t soft -o soft.stl dicom_dir

# Control mesh quality (more smoothing, less reduction)
dicom2stl -t bone --smooth 50 --reduce 0.5 -o bone.stl dicom.zip

# Custom threshold values (4 values: t1, t2, t3, t4)
dicom2stl --double "100;200;300;400" -o custom.stl dicom.zip
```

**Interactive Tutorial:**

Try the interactive Jupyter notebook via Binder:

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/dave3d/dicom2stl/main?filepath=examples%2FIsosurface.ipynb)

Troubleshooting
===============

**Common Issues:**

- **"No valid input given"** - Check that your DICOM files have the `.dcm` extension
- **Empty or incorrect mesh** - Try adjusting the tissue type or using custom threshold values
- **Out of memory** - The shrink filter is enabled by default to reduce memory usage. For very large datasets, consider processing on a machine with more RAM
- **Slice ordering issues** - Always use a zip file or directory rather than individual DICOM files on the command line

**Getting Help:**

- Run `dicom2stl --help` for all options
- Check the [examples](examples/) folder for sample code
- Report issues on [GitHub](https://github.com/dave3d/dicom2stl/issues)

Contributing
============

Contributions are welcome! Please feel free to submit a Pull Request.
