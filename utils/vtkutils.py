#! /usr/bin/env python


"""
A collection of VTK functions for processing surfaces and volume.

Written by David T. Chen from the National Institute of Allergy and
Infectious Diseases, dchen@mail.nih.gov.
It is covered by the Apache License, Version 2.0:
http://www.apache.org/licenses/LICENSE-2.0
"""

from __future__ import print_function

# import gc
import sys
import time
import traceback

import vtk


def elapsedTime(start_time):
    dt = time.perf_counter() - start_time
    print("    %4.3f seconds", dt)


#
#  Isosurface extraction
#
def extractSurface(vol, isovalue=0.0):
    """Extract an isosurface from a volume."""
    try:
        t = time.perf_counter()
        iso = vtk.vtkContourFilter()
        if vtk.vtkVersion.GetVTKMajorVersion() >= 6:
            iso.SetInputData(vol)
        else:
            iso.SetInput(vol)
        iso.SetValue(0, isovalue)
        iso.Update()
        print("Surface extracted")
        mesh = iso.GetOutput()
        print("    ", mesh.GetNumberOfPolys(), "polygons")
        elapsedTime(t)
        iso = None
        return mesh
    except BaseException:
        print("Iso-surface extraction failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


#
#  Mesh filtering
#
def cleanMesh(mesh, connectivityFilter=False):
    """Clean a mesh using VTK's CleanPolyData filter."""
    try:
        t = time.perf_counter()
        connect = vtk.vtkPolyDataConnectivityFilter()
        clean = vtk.vtkCleanPolyData()

        if connectivityFilter:
            if vtk.vtkVersion.GetVTKMajorVersion() >= 6:
                connect.SetInputData(mesh)
            else:
                connect.SetInput(mesh)
            connect.SetExtractionModeToLargestRegion()
            clean.SetInputConnection(connect.GetOutputPort())
        else:
            if vtk.vtkVersion.GetVTKMajorVersion() >= 6:
                clean.SetInputData(mesh)
            else:
                clean.SetInput(mesh)

        clean.Update()
        print("Surface cleaned")
        m2 = clean.GetOutput()
        print("    ", m2.GetNumberOfPolys(), "polygons")
        elapsedTime(t)
        clean = None
        connect = None
        return m2
    except BaseException:
        print("Surface cleaning failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


def smoothMesh(mesh, nIterations=10):
    """Smooth a mesh using VTK's WindowedSincPolyData filter."""
    try:
        t = time.perf_counter()
        smooth = vtk.vtkWindowedSincPolyDataFilter()
        smooth.SetNumberOfIterations(nIterations)
        if vtk.vtkVersion.GetVTKMajorVersion() >= 6:
            smooth.SetInputData(mesh)
        else:
            smooth.SetInput(mesh)
        smooth.Update()
        print("Surface smoothed")
        m2 = smooth.GetOutput()
        print("    ", m2.GetNumberOfPolys(), "polygons")
        elapsedTime(t)
        smooth = None
        return m2
    except BaseException:
        print("Surface smoothing failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


def rotateMesh(mesh, axis=1, angle=0):
    """Rotate a mesh about an arbitrary axis.  Angle is in degrees."""
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
        if vtk.vtkVersion.GetVTKMajorVersion() >= 6:
            tfilter.SetInputData(mesh)
        else:
            tfilter.SetInput(mesh)
        tfilter.Update()
        mesh2 = tfilter.GetOutput()
        return mesh2
    except BaseException:
        print("Surface rotating failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


# @profile


def reduceMesh(mymesh, reductionFactor):
    """Reduce the number of triangles in a mesh using VTK's vtkDecimatePro
    filter."""
    try:
        t = time.perf_counter()
        # deci = vtk.vtkQuadricDecimation()
        deci = vtk.vtkDecimatePro()
        deci.SetTargetReduction(reductionFactor)
        if vtk.vtkVersion.GetVTKMajorVersion() >= 6:
            deci.SetInputData(mymesh)
        else:
            deci.SetInput(mymesh)
        deci.Update()
        print("Surface reduced")
        m2 = deci.GetOutput()
        del deci
        #        deci = None
        print("    ", m2.GetNumberOfPolys(), "polygons")
        elapsedTime(t)
        return m2
    except BaseException:
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
            if region_sizes.GetValue(i) > max_size:
                max_size = region_sizes.GetValue(i)

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

    except BaseException:
        print("Remove small objects failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )


#
#   Mesh I/O
#


def readMesh(name):
    """Read a mesh. Uses suffix to determine specific file type reader."""
    if name.endswith(".vtk"):
        return readVTKMesh(name)
    if name.endswith(".ply"):
        return readPLY(name)
    if name.endswith(".stl"):
        return readSTL(name)
    print("Unknown file type: ", name)
    return None


def readVTKMesh(name):
    """Read a VTK mesh file."""
    try:
        reader = vtk.vtkPolyDataReader()
        reader.SetFileName(name)
        reader.Update()
        print("Input mesh:", name)
        mesh = reader.GetOutput()
        del reader
        #        reader = None
        return mesh
    except BaseException:
        print("VTK mesh reader failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


def readSTL(name):
    """Read an STL mesh file."""
    try:
        reader = vtk.vtkSTLReader()
        reader.SetFileName(name)
        reader.Update()
        print("Input mesh:", name)
        mesh = reader.GetOutput()
        del reader
        #        reader = None
        return mesh
    except BaseException:
        print("STL Mesh reader failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


def readPLY(name):
    """Read a PLY mesh file."""
    try:
        reader = vtk.vtkPLYReader()
        reader.SetFileName(name)
        reader.Update()
        print("Input mesh:", name)
        mesh = reader.GetOutput()
        del reader
        #        reader = None
        return mesh
    except BaseException:
        print("PLY Mesh reader failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


def writeMesh(mesh, name):
    """Write a mesh. Uses suffix to determine specific file type writer."""
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
    print("Unknown file type: ", name)


def writeVTKMesh(mesh, name):
    """Write a VTK mesh file."""
    try:
        writer = vtk.vtkPolyDataWriter()
        if vtk.vtkVersion.GetVTKMajorVersion() >= 6:
            writer.SetInputData(mesh)
        else:
            writer.SetInput(mesh)
        writer.SetFileTypeToBinary()
        writer.SetFileName(name)
        writer.Write()
        print("Output mesh:", name)
        writer = None
    except BaseException:
        print("VTK mesh writer failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


def writeSTL(mesh, name):
    """Write an STL mesh file."""
    try:
        writer = vtk.vtkSTLWriter()
        if vtk.vtkVersion.GetVTKMajorVersion() >= 6:
            print("writeSTL 1")
            writer.SetInputData(mesh)
        else:
            print("writeSTL 2")
            writer.SetInput(mesh)
        writer.SetFileTypeToBinary()
        writer.SetFileName(name)
        writer.Write()
        print("Output mesh:", name)
        writer = None
    except BaseException:
        print("STL mesh writer failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


def writePLY(mesh, name):
    """Read a PLY mesh file."""
    try:
        writer = vtk.vtkPLYWriter()
        if vtk.vtkVersion.GetVTKMajorVersion() >= 6:
            writer.SetInputData(mesh)
        else:
            writer.SetInput(mesh)
        writer.SetFileTypeToBinary()
        writer.SetFileName(name)
        writer.Write()
        print("Output mesh:", name)
        writer = None
    except BaseException:
        print("PLY mesh writer failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


#
#  Volume I/O
#


def readVTKVolume(name):
    """Read a VTK volume image file. Returns a vtkStructuredPoints object."""
    try:
        reader = vtk.vtkStructuredPointsReader()
        reader.SetFileName(name)
        reader.Update()
        print("Input volume:", name)
        vol = reader.GetOutput()
        reader = None
        return vol
    except BaseException:
        print("VTK volume reader failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


def writeVTKVolume(vtkimg, name):
    """Write the old VTK Image file format"""
    try:
        writer = vtk.vtkStructuredPointsWriter()
        writer.SetFileName(name)
        writer.SetInputData(vtkimg)
        writer.SetFileTypeToBinary()
        writer.Update()
    except BaseException:
        print("VTK volume writer failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )


def readVTIVolume(name):
    """Read a VTK XML volume image file. Returns a vtkStructuredPoints object."""
    try:
        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(name)
        reader.Update()
        print("Input volume:", name)
        vol = reader.GetOutput()
        reader = None
        return vol
    except BaseException:
        print("VTK XML volume reader failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )
    return None


def writeVTIVolume(vtkimg, name):
    """Write the new XML VTK Image file format"""
    try:
        writer = vtk.vtkXMLImageDataWriter()
        writer.SetFileName(name)
        writer.SetInputData(vtkimg)
        writer.Update()
    except BaseException:
        print("VTK volume writer failed")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
        )


# @profile


def memquery1():
    print("Hiya 1")


# @profile


def memquery2():
    print("Hiya 2")


# @profile


def memquery3():
    print("Hiya 3")


#
#  Main (test code)
#
if __name__ == "__main__":
    print("vtkutils.py")

    print("VTK version:", vtk.vtkVersion.GetVTKVersion())
    print("VTK:", vtk)

    try:
        mesh = readMesh(sys.argv[1])
        #       mesh = readMesh("models/soft.stl")
        #       mesh = cleanMesh(mesh, False)
        #       mesh = smoothMesh(mesh)
        mesh2 = reduceMesh(mesh, 0.50)
        #        writeMesh(mesh2, "soft.ply")
        writeMesh(mesh2, sys.argv[2])
    except BaseException:
        print("Usage: vtkutils.py input_mesh output_mesh")
