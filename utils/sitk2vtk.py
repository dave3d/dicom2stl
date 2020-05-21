#! /usr/bin/env python

"""
Function to convert a SimpleITK image to a VTK image.

Written by David T. Chen from the National Institute of Allergy
and Infectious Diseases, dchen@mail.nih.gov.
It is covered by the Apache License, Version 2.0:
http://www.apache.org/licenses/LICENSE-2.0
"""

from __future__ import print_function
from copy import *
import SimpleITK as sitk
import vtk
from numpy import *

# Adapted from the VTK example
# http://www.vtk.org/Wiki/VTK/Examples/Python/vtkWithNumpy


# dictionary to convert SimpleITK pixel types to VTK
#
pixelmap = {sitk.sitkUInt8:   vtk.VTK_UNSIGNED_CHAR,  sitk.sitkInt8:    vtk.VTK_CHAR,
            sitk.sitkUInt16:  vtk.VTK_UNSIGNED_SHORT, sitk.sitkInt16:   vtk.VTK_SHORT,
            sitk.sitkUInt32:  vtk.VTK_UNSIGNED_INT,   sitk.sitkInt32:   vtk.VTK_INT,
            sitk.sitkUInt64:  vtk.VTK_UNSIGNED_LONG,  sitk.sitkInt64:   vtk.VTK_LONG,
            sitk.sitkFloat32: vtk.VTK_FLOAT,          sitk.sitkFloat64: vtk.VTK_DOUBLE,

            sitk.sitkVectorUInt8:   vtk.VTK_UNSIGNED_CHAR,  sitk.sitkVectorInt8:    vtk.VTK_CHAR,
            sitk.sitkVectorUInt16:  vtk.VTK_UNSIGNED_SHORT, sitk.sitkVectorInt16:   vtk.VTK_SHORT,
            sitk.sitkVectorUInt32:  vtk.VTK_UNSIGNED_INT,   sitk.sitkVectorInt32:   vtk.VTK_INT,
            sitk.sitkVectorUInt64:  vtk.VTK_UNSIGNED_LONG,  sitk.sitkVectorInt64:   vtk.VTK_LONG,
            sitk.sitkVectorFloat32: vtk.VTK_FLOAT,          sitk.sitkVectorFloat64: vtk.VTK_DOUBLE,

            sitk.sitkLabelUInt8:  vtk.VTK_UNSIGNED_CHAR,
            sitk.sitkLabelUInt16: vtk.VTK_UNSIGNED_SHORT,
            sitk.sitkLabelUInt32: vtk.VTK_UNSIGNED_INT,
            sitk.sitkLabelUInt64: vtk.VTK_UNSIGNED_LONG,
            }


def sitk2vtk(img, outVol=None, debugOn=False):
    """Convert a SimpleITK image to a VTK image, via numpy."""

    size = list(img.GetSize())
    origin = list(img.GetOrigin())
    spacing = list(img.GetSpacing())
    sitktype = img.GetPixelID()
    try:
        vtktype = pixelmap[sitktype]
    except:
        print("Unsupported type: ", sitktype, ", ", img.GetPixelIDTypeAsString(), sep='')
        return None
    ncomp = img.GetNumberOfComponentsPerPixel()

    if len(size)>3:
        print("Dimensions>3 not supported")
        return None

    # there doesn't seem to be a way to specify the image orientation in VTK

    # convert the SimpleITK image to a numpy array
    i2 = sitk.GetArrayFromImage(img)
    i2_string = i2.tostring()
    if debugOn:
        print("data string address inside sitk2vtk", hex(id(i2_string)))

    # send the numpy array to VTK with a vtkImageImport object
    dataImporter = vtk.vtkImageImport()

    dataImporter.CopyImportVoidPointer(i2_string, len(i2_string))

    dataImporter.SetDataScalarType(vtktype)

    dataImporter.SetNumberOfScalarComponents(ncomp)

    # VTK expects 3-dimensional parameters
    if len(size) == 2:
        size.append(1)

    if len(origin) == 2:
        origin.append(0.0)

    if len(spacing) == 2:
        spacing.append(spacing[0])

    # Set the new VTK image's parameters
    #
    dataImporter.SetDataExtent(0, size[0]-1, 0, size[1]-1, 0, size[2]-1)
    dataImporter.SetWholeExtent(0, size[0]-1, 0, size[1]-1, 0, size[2]-1)

    dataImporter.SetDataOrigin(origin)
    dataImporter.SetDataSpacing(spacing)

    dataImporter.Update()

    vtk_image = dataImporter.GetOutput()

    # outVol and this DeepCopy are a work-around to avoid a crash on Windows
    if outVol is not None:
        outVol.DeepCopy(vtk_image)

    if debugOn:
        print("Volume object inside sitk2vtk")
        print(vtk_image)
        print("type = ", vtktype)
        print("num components = ", ncomp)
        print(size)
        print(origin)
        print(spacing)
        print(vtk_image.GetScalarComponentAsFloat(0, 0, 0, 0))

    return vtk_image


