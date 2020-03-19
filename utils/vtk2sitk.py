#!/usr/bin/env python

import SimpleITK as sitk
import numpy
import vtk
from vtk.util.numpy_support import *

def vtk2sitk(vtkimg, debug=False):
    """Takes a VTK image, returns a SimpleITK image."""
    sd = vtkimg.GetPointData().GetScalars()
    npdata = vtk_to_numpy(sd)

    dims = list(vtkimg.GetDimensions())
    origin = vtkimg.GetOrigin()
    spacing=vtkimg.GetSpacing()

    if debug:
        print("dims:", dims)
        print("origin:", origin)
        print("spacing:", spacing)

        print("numpy type:", npdata.dtype)
        print("numpy shape:", npdata.shape)

    dims.reverse()
    npdata.shape=tuple(dims)
    if debug:
        print("new shape:", npdata.shape)
    sitkimg = sitk.GetImageFromArray(npdata)
    sitkimg.SetSpacing(spacing)
    return sitkimg
