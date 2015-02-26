dicom2stl
=========
dicom2stl.py is a script that takes a Dicom series and generates a STL surface mesh.

Written by David T. Chen from the National Library of Medicine, dchen@mail.nih.gov
It is covered by the Apache License, Version 2.0:
> http://www.apache.org/licenses/LICENSE-2.0

Required packages
=================
The script is written in Python and uses 2 external packages, vtk and SimpleITK.

vtk can be downloaded and built from the following repository:
> https://github.com/Kitware/VTK

On some Linux distributions it can be installed with the following command:
> sudo apt-get install vtk

SimpleITK can be installed via the following command:
> easy_install vtk

The options for the script can be seen by running it:
> vtkpython dicom2stl.py --help


How it works
============
First the script reads in a series of 2-d images or a simple 3-d image.  It can read
any format supported by ITK.  If the input name is a zip file or a directory name,
the script expects a single series of DCM images, all with the ".dcm" suffix.

Note: if you run this script with the individual Dicom slices provided on the
command line, they might not be ordered in the correct order.  You are better
off providing a zip file or a directory.  Dicom slices are not necessarily
ordered the same alphabetically as they are physically.  In the case of a zip file
or directory, the script loads using the SimpleITK ImageSeriesReader class,
which orders the slices by their physical layout, not their alphabetical names.

The primary image processing pipeline is as follows:
* Shrink the volume to 256 max dim (enabled by default)
* Anisotropic smoothing (disabled by default)
* Double threshold filter (enabled when tissue types are used)
* Median filter (enabled for 'soft' and 'fat' tissue types)
* Pad volume

The script has built in double threshold values for the 4 different tissue types (bone, skin, muscle, soft).
These values assume the input is DICOM with standard CT Hounsfield units.  I determined these values experimentally
on a few DICOM test sets I had, so how well they work for others is in question.

The volume is shrunk to 256 cubed or less for speed and polygon count reasons.

After all the image processing is finished, the volume is converted to a VTK image using sitk2vtk.py.

Then the following VTK pipeline is executed:
* Extract a surface mesh from the VTK image
* Apply the clean mesh filter
* Apply the smooth mesh filter
* Apply the reduce mesh filter
* Write out an STL file

The amount of smoothing and mesh reduction can be adjusted via command line options.  By default
25 iterations of smoothing is applied and the number of vertices is reduced by 90%.


Examples
========

To extract the bone from a zip of dicom images:
> vtkpython dicom2stl.py -t bone -o bone.stl dicom.zip

To extract the skin from a NRRD volume:
> vtkpython dicom2stl.py -t skin -o skin.stl volume.nrrd

To extract a specific iso-value from a VTK volume:
> vtkpython dicom2stl.py -t 128 -o iso.stl volume.vtk

To extract soft tissue from a dicom series in directory and
apply a 180 degree Y axis rotation:
> vtkpython dicom2stl.py --enable rotation -t soft_tissue -o soft.stl dicom_dir

