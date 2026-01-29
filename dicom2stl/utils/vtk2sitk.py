#!/usr/bin/env python

""" function for converting a VTK image to a SimpleITK image """

import SimpleITK as sitk
import vtk
from vtk.util import numpy_support


def vtk2sitk(vtk_image: vtk.vtkImageData, debug: bool = False) -> sitk.Image:
    """Convert a VTK image to a SimpleITK image, via numpy.
    
    This function performs the reverse conversion of sitk2vtk, handling coordinate
    system differences:
    - VTK uses XYZ ordering for dimensions, spacing, and extent
    - Numpy arrays are created in C-order from flattened VTK data
    - Dimensions are reversed to match SimpleITK/ITK conventions (ZYX → XYZ)
    - SimpleITK uses ITK conventions with physical space coordinates
    
    The function also:
    - Extracts scalar data from VTK point data
    - Preserves image origin, spacing, and direction matrix (VTK 9+)
    - Reshapes numpy array to match reversed dimensions
    
    Args:
        vtk_image: VTK image data object to convert
        debug: If True, print debug information about the conversion
        
    Returns:
        SimpleITK image with the same voxel data and metadata
    """
    scalars = vtk_image.GetPointData().GetScalars()
    numpy_array = numpy_support.vtk_to_numpy(scalars)

    dims = list(vtk_image.GetDimensions())
    origin = vtk_image.GetOrigin()
    spacing = vtk_image.GetSpacing()

    if debug:
        print("dims:", dims)
        print("origin:", origin)
        print("spacing:", spacing)
        print("numpy type:", numpy_array.dtype)
        print("numpy shape:", numpy_array.shape)

    dims.reverse()
    numpy_array.shape = tuple(dims)
    if debug:
        print("new shape:", numpy_array.shape)
    sitk_image = sitk.GetImageFromArray(numpy_array)
    sitk_image.SetSpacing(spacing)
    sitk_image.SetOrigin(origin)

    if vtk.vtkVersion.GetVTKMajorVersion() >= 9:
        direction_matrix = vtk_image.GetDirectionMatrix()
        direction = [direction_matrix.GetElement(y, x) 
                    for y in range(3) for x in range(3)]
        sitk_image.SetDirection(direction)
    
    return sitk_image
