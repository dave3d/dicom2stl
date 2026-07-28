#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "dicom2stl",
#   "SimpleITK>=2.5.3",
#   "vtk>=9.5.2",
# ]
# ///

"""Unit tests for VTK utility functions."""

import os
import unittest

import SimpleITK as sitk
import create_data
import vtk
from dicom2stl.utils import vtkutils


class TestVTKUtils(unittest.TestCase):
    """Test suite for VTK utility functions."""
    BALL = None

    @classmethod
    def setUpClass(cls):
        print("Setting it up")
        sphere = vtk.vtkSphereSource()
        sphere.SetPhiResolution(16)
        sphere.SetThetaResolution(16)
        sphere.Update()
        connect = vtk.vtkPolyDataConnectivityFilter()
        if vtk.vtkVersion.GetVTKMajorVersion() >= 6:
            connect.SetInputData(sphere.GetOutput())
        else:
            connect.SetInput(sphere)
        connect.SetExtractionModeToLargestRegion()
        connect.Update()
        TestVTKUtils.BALL = connect.GetOutput()
        # print(TestVTKUtils.BALL)

    @classmethod
    def tearDownClass(cls):
        print("Tearing it down")
        try:
            os.remove("ball.stl")
            os.remove("ball.vtk")
            os.remove("ball.ply")
        except OSError:
            print("")

    def test_cleanMesh(self):
        """Test cleaning mesh with optional connectivity filtering."""
        result = vtkutils.cleanMesh(TestVTKUtils.BALL, False)
        print(result.GetNumberOfPolys())
        result = vtkutils.cleanMesh(TestVTKUtils.BALL, True)
        print(result.GetNumberOfPolys())

    def test_smoothMesh(self):
        """Test mesh smoothing."""
        result = vtkutils.smoothMesh(TestVTKUtils.BALL)
        print(result.GetNumberOfPolys())

    def test_rotateMesh(self):
        """Test mesh rotation."""
        result = vtkutils.rotateMesh(TestVTKUtils.BALL, 0, 30)
        print(result.GetNumberOfPolys())

    def test_reduceMesh(self):
        """Test mesh decimation/reduction."""
        result = vtkutils.reduceMesh(TestVTKUtils.BALL, 0.5)
        print(result.GetNumberOfPolys())

    def test_meshIO(self):
        """Test mesh input/output operations."""
        try:
            vtkutils.writeMesh(TestVTKUtils.BALL, "ball.stl")
            vtkutils.writeMesh(TestVTKUtils.BALL, "ball.vtk")
            vtkutils.writeMesh(TestVTKUtils.BALL, "ball.ply")
        except (RuntimeError, IOError):
            print("Bad write")
            self.fail("writeMesh failed")

        try:
            m = vtkutils.readMesh("ball.stl")
            print("Read", m.GetNumberOfPolys(), "polygons")
            m = vtkutils.readMesh("ball.vtk")
            print("Read", m.GetNumberOfPolys(), "polygons")
            m = vtkutils.readMesh("ball.ply")
            print("Read", m.GetNumberOfPolys(), "polygons")
        except (RuntimeError, IOError):
            print("Bad read")
            self.fail("readMesh failed")

    def test_readVTKVolume(self):
        """Test reading VTK volume files."""
        tetra = create_data.make_tetra(32)
        sitk.WriteImage(tetra, "tetra.vtk")
        try:
            vtkvol = vtkutils.readVTKVolume("tetra.vtk")
            print(type(vtkvol))
            print(vtkvol.GetDimensions())
        except (RuntimeError, IOError):
            self.fail("readVTKVolume failed")

        try:
            os.remove("tetra.vtk")
        except OSError:
            print("remove tetra.vtk failed")


if __name__ == "__main__":
    unittest.main()
