#! /usr/bin/env python


"""
A collection of VTK functions for processing surfaces and volume.

Written by David T. Chen from the National Institute of Allergy and
Infectious Diseases, dchen@mail.nih.gov.
It is covered by the Apache License, Version 2.0:
http://www.apache.org/licenses/LICENSE-2.0
"""

from __future__ import print_function

import sys
import time
import traceback
from typing import Optional

import vtk


def elapsedTime(start_time: float) -> None:
    """Print the elapsed time since start_time."""
    dt = time.perf_counter() - start_time
    print(f"    {dt:4.3f} seconds")


#
#  Isosurface extraction
#
def extractSurface(vol: vtk.vtkImageData, isovalue: float = 0.0) -> Optional[vtk.vtkPolyData]:
    """Extract an isosurface from a volume using the marching cubes algorithm.
    
    Args:
        vol: VTK image data volume
        isovalue: Threshold value for the isosurface
        
    Returns:
        Surface mesh as vtkPolyData, or None if extraction fails
    """
    try:
        t = time.perf_counter()
        iso = vtk.vtkContourFilter()
        iso.SetInputData(vol)
        iso.SetValue(0, isovalue)
        iso.Update()
        print("Surface extracted")
        mesh = iso.GetOutput()
        print("    ", mesh.GetNumberOfPolys(), "polygons")
        elapsedTime(t)
        iso = None
        return mesh
    except RuntimeError:
        print("Iso-surface extraction failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


#
#  Mesh filtering
#
def cleanMesh(mesh: vtk.vtkPolyData, connectivityFilter: bool = False) -> Optional[vtk.vtkPolyData]:
    """Clean a mesh using VTK's CleanPolyData filter.
    
    Args:
        mesh: Input mesh to clean
        connectivityFilter: If True, extract only the largest connected region
        
    Returns:
        Cleaned mesh, or None if cleaning fails
    """
    try:
        t = time.perf_counter()
        connect = vtk.vtkPolyDataConnectivityFilter()
        clean = vtk.vtkCleanPolyData()

        if connectivityFilter:
            connect.SetInputData(mesh)
            connect.SetExtractionModeToLargestRegion()
            clean.SetInputConnection(connect.GetOutputPort())
        else:
            clean.SetInputData(mesh)

        clean.Update()
        print("Surface cleaned")
        m2 = clean.GetOutput()
        print("    ", m2.GetNumberOfPolys(), "polygons")
        elapsedTime(t)
        clean = None
        connect = None
        return m2
    except RuntimeError:
        print("Surface cleaning failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


def smoothMesh(mesh: vtk.vtkPolyData, nIterations: int = 10) -> Optional[vtk.vtkPolyData]:
    """Smooth a mesh using VTK's WindowedSincPolyData filter.
    
    Args:
        mesh: Input mesh to smooth
        nIterations: Number of smoothing iterations
        
    Returns:
        Smoothed mesh, or None if smoothing fails
    """
    try:
        t = time.perf_counter()
        smooth = vtk.vtkWindowedSincPolyDataFilter()
        smooth.SetNumberOfIterations(nIterations)
        smooth.SetInputData(mesh)
        smooth.Update()
        print("Surface smoothed")
        m2 = smooth.GetOutput()
        print("    ", m2.GetNumberOfPolys(), "polygons")
        elapsedTime(t)
        smooth = None
        return m2
    except RuntimeError:
        print("Surface smoothing failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


def rotateMesh(mesh: vtk.vtkPolyData, axis: int = 1, angle: float = 0) -> Optional[vtk.vtkPolyData]:
    """Rotate a mesh about an arbitrary axis.
    
    Args:
        mesh: Input mesh to rotate
        axis: Rotation axis (0=X, 1=Y, 2=Z)
        angle: Rotation angle in degrees
        
    Returns:
        Rotated mesh, or None if rotation fails
    """
    try:
        print("Rotating surface: axis=", axis, "angle=", angle)
        matrix = vtk.vtkTransform()
        if axis == 0:
            matrix.RotateX(angle)
        if axis == 1:
            matrix.RotateY(angle)
        if axis == 2:
            matrix.RotateZ(angle)
        tfilter = vtk.vtkTransformPolyDataFilter()
        tfilter.SetTransform(matrix)
        tfilter.SetInputData(mesh)
        tfilter.Update()
        mesh2 = tfilter.GetOutput()
        return mesh2
    except RuntimeError:
        print("Surface rotating failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


def reduceMesh(mesh: vtk.vtkPolyData, reductionFactor: float) -> Optional[vtk.vtkPolyData]:
    """Reduce the number of triangles in a mesh using VTK's vtkDecimatePro filter.
    
    Args:
        mesh: Input mesh to reduce
        reductionFactor: Target reduction as a fraction (0.0 to 1.0)
        
    Returns:
        Reduced mesh, or None if reduction fails
    """
    try:
        t = time.perf_counter()
        deci = vtk.vtkDecimatePro()
        deci.SetTargetReduction(reductionFactor)
        deci.SetInputData(mesh)
        deci.Update()
        print("Surface reduced")
        m2 = deci.GetOutput()
        del deci
        print("    ", m2.GetNumberOfPolys(), "polygons")
        elapsedTime(t)
        return m2
    except RuntimeError:
        print("Surface reduction failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


# from https://github.com/AOT-AG/DicomToMesh/blob/master/lib/src/meshRoutines.cpp#L109
# MIT License
def removeSmallObjects(mesh, ratio):
    """
    Remove small parts which are not of interest
    @param ratio A floating-point value between 0.0 and 1.0, the higher the stronger effect
    """

    # do nothing if ratio is 0
    if ratio == 0:
        return mesh

    try:
        t = time.perf_counter()
        conn_filter = vtk.vtkPolyDataConnectivityFilter()
        conn_filter.SetInputData(mesh)
        conn_filter.SetExtractionModeToAllRegions()
        conn_filter.Update()

        # remove objects consisting of less than ratio vertexes of the biggest object
        region_sizes = conn_filter.GetRegionSizes()

        # find object with most vertices
        max_size = 0
        for i in range(conn_filter.GetNumberOfExtractedRegions()):
            max_size = max(max_size, region_sizes.GetValue(i))

        # append regions of sizes over the threshold
        conn_filter.SetExtractionModeToSpecifiedRegions()
        for i in range(conn_filter.GetNumberOfExtractedRegions()):
            if region_sizes.GetValue(i) > max_size * ratio:
                conn_filter.AddSpecifiedRegion(i)

        conn_filter.Update()
        processed_mesh = conn_filter.GetOutput()
        print("Small parts cleaned")
        print("    ", processed_mesh.GetNumberOfPolys(), "polygons")
        elapsedTime(t)
        return processed_mesh

    except RuntimeError:
        print("Remove small objects failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


#
#   Mesh I/O
#


def readMesh(name: str) -> Optional[vtk.vtkPolyData]:
    """Read a mesh from file. Uses suffix to determine file type.
    
    Supported formats: .vtk, .ply, .stl
    
    Args:
        name: Path to mesh file
        
    Returns:
        Mesh as vtkPolyData, or None if reading fails
    """
    if name.endswith(".vtk"):
        return readVTKMesh(name)
    if name.endswith(".ply"):
        return readPLY(name)
    if name.endswith(".stl"):
        return readSTL(name)
    print("Unknown file type:", name)
    return None


def readVTKMesh(name: str) -> Optional[vtk.vtkPolyData]:
    """Read a VTK mesh file.
    
    Args:
        name: Path to VTK file
        
    Returns:
        Mesh as vtkPolyData, or None if reading fails
    """
    try:
        reader = vtk.vtkPolyDataReader()
        reader.SetFileName(name)
        reader.Update()
        print("Input mesh:", name)
        mesh = reader.GetOutput()
        del reader
        return mesh
    except RuntimeError:
        print("VTK mesh reader failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


def readSTL(name: str) -> Optional[vtk.vtkPolyData]:
    """Read an STL mesh file.
    
    Args:
        name: Path to STL file
        
    Returns:
        Mesh as vtkPolyData, or None if reading fails
    """
    try:
        reader = vtk.vtkSTLReader()
        reader.SetFileName(name)
        reader.Update()
        print("Input mesh:", name)
        mesh = reader.GetOutput()
        del reader
        return mesh
    except RuntimeError:
        print("STL mesh reader failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


def readPLY(name: str) -> Optional[vtk.vtkPolyData]:
    """Read a PLY mesh file.
    
    Args:
        name: Path to PLY file
        
    Returns:
        Mesh as vtkPolyData, or None if reading fails
    """
    try:
        reader = vtk.vtkPLYReader()
        reader.SetFileName(name)
        reader.Update()
        print("Input mesh:", name)
        mesh = reader.GetOutput()
        del reader
        #        reader = None
        return mesh
    except RuntimeError:
        print("PLY Mesh reader failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


def writeMesh(mesh: vtk.vtkPolyData, name: str) -> None:
    """Write a mesh to file. Uses suffix to determine file type.
    
    Supported formats: .vtk, .ply, .stl
    
    Args:
        mesh: Mesh to write
        name: Output file path
    """
    print("Writing", mesh.GetNumberOfPolys(), "polygons to", name)
    if name.endswith(".vtk"):
        writeVTKMesh(mesh, name)
        return
    if name.endswith(".ply"):
        writePLY(mesh, name)
        return
    if name.endswith(".stl"):
        writeSTL(mesh, name)
        return
    print("Unknown file type:", name)


def writeVTKMesh(mesh: vtk.vtkPolyData, name: str) -> None:
    """Write a VTK mesh file.
    
    Args:
        mesh: Mesh to write
        name: Output VTK file path
    """
    try:
        writer = vtk.vtkPolyDataWriter()
        writer.SetInputData(mesh)
        writer.SetFileTypeToBinary()
        writer.SetFileName(name)
        writer.Write()
        print("Output mesh:", name)
        writer = None
    except RuntimeError:
        print("VTK mesh writer failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )


def writeSTL(mesh: vtk.vtkPolyData, name: str) -> None:
    """Write an STL mesh file.
    
    Args:
        mesh: Mesh to write
        name: Output STL file path
    """
    try:
        writer = vtk.vtkSTLWriter()
        writer.SetInputData(mesh)
        writer.SetFileTypeToBinary()
        writer.SetFileName(name)
        writer.Write()
        print("Output mesh:", name)
        writer = None
    except RuntimeError:
        print("STL mesh writer failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )


def writePLY(mesh: vtk.vtkPolyData, name: str) -> None:
    """Write a PLY mesh file.
    
    Args:
        mesh: Mesh to write
        name: Output PLY file path
    """
    try:
        writer = vtk.vtkPLYWriter()
        writer.SetInputData(mesh)
        writer.SetFileTypeToBinary()
        writer.SetFileName(name)
        writer.Write()
        print("Output mesh:", name)
        writer = None
    except RuntimeError:
        print("PLY mesh writer failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )


#
#  Volume I/O
#


def readVTKVolume(name: str) -> Optional[vtk.vtkStructuredPoints]:
    """Read a VTK volume image file.
    
    Args:
        name: Path to VTK volume file
        
    Returns:
        Volume as vtkStructuredPoints, or None if reading fails
    """
    try:
        reader = vtk.vtkStructuredPointsReader()
        reader.SetFileName(name)
        reader.Update()
        print("Input volume:", name)
        vol = reader.GetOutput()
        reader = None
        return vol
    except RuntimeError:
        print("VTK volume reader failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


def writeVTKVolume(vtkimg: vtk.vtkImageData, name: str) -> None:
    """Write the old VTK Image file format.
    
    Args:
        vtkimg: Volume to write
        name: Output file path
    """
    try:
        writer = vtk.vtkStructuredPointsWriter()
        writer.SetFileName(name)
        writer.SetInputData(vtkimg)
        writer.SetFileTypeToBinary()
        writer.Update()
    except RuntimeError:
        print("VTK volume writer failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )


def readVTIVolume(name: str) -> Optional[vtk.vtkImageData]:
    """Read a VTK XML volume image file.
    
    Args:
        name: Path to VTI file
        
    Returns:
        Volume as vtkImageData, or None if reading fails
    """
    try:
        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(name)
        reader.Update()
        print("Input volume:", name)
        vol = reader.GetOutput()
        reader = None
        return vol
    except RuntimeError:
        print("VTK XML volume reader failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


def writeVTIVolume(vtkimg: vtk.vtkImageData, name: str) -> None:
    """Write the new XML VTK Image file format.
    
    Args:
        vtkimg: Volume to write
        name: Output VTI file path
    """
    try:
        writer = vtk.vtkXMLImageDataWriter()
        writer.SetFileName(name)
        writer.SetInputData(vtkimg)
        writer.Update()
    except RuntimeError:
        print("VTK volume writer failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )


if __name__ == "__main__":
    print("vtkutils.py")
    print("VTK version:", vtk.vtkVersion.GetVTKVersion())
    
    if len(sys.argv) != 3:
        print("Usage: vtkutils.py input_mesh output_mesh")
        sys.exit(1)
    
    try:
        inmesh = readMesh(sys.argv[1])
        if inmesh:
            inmesh2 = reduceMesh(inmesh, 0.50)
            if inmesh2:
                writeMesh(inmesh2, sys.argv[2])
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
