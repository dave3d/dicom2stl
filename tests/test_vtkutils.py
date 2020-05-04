#! /usr/bin/env python

import unittest
from utils import vtkutils
import vtk
import SimpleITK as sitk
import os
import create_data

class TestVTKUtils(unittest.TestCase):

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
        #print(TestVTKUtils.BALL)

    @classmethod
    def tearDownClass(cls):
        print("Tearing it down")
        try:
            os.remove("ball.stl")
            os.remove("ball.vtk")
            os.remove("ball.ply")
        except:
            print("")

    def test_cleanMesh(self):
        print("Testing cleanMesh")
        result = vtkutils.cleanMesh(TestVTKUtils.BALL, False)
        print(result.GetNumberOfPolys())
        result = vtkutils.cleanMesh(TestVTKUtils.BALL, True)
        print(result.GetNumberOfPolys())

    def test_smoothMesh(self):
        print("Testing smoothMesh")
        result = vtkutils.smoothMesh(TestVTKUtils.BALL)
        print(result.GetNumberOfPolys())

    def test_rotateMesh(self):
        print("Testing rotateMesh")
        result = vtkutils.rotateMesh(TestVTKUtils.BALL, 0, 30)
        print(result.GetNumberOfPolys())

    def test_reduceMesh(self):
        print("Testing reduceMesh")
        result = vtkutils.reduceMesh(TestVTKUtils.BALL, .5)
        print(result.GetNumberOfPolys())

    def test_meshIO(self):
        print("Testing Mesh I/O")
        try:
            vtkutils.writeMesh(TestVTKUtils.BALL, "ball.stl")
            vtkutils.writeMesh(TestVTKUtils.BALL, "ball.vtk")
            vtkutils.writeMesh(TestVTKUtils.BALL, "ball.ply")
        except:
            print("Bad write")
            self.fail("writeMesh failed")

        try:
            m = vtkutils.readMesh("ball.stl")
            print("Read", m.GetNumberOfPolys(), "polygons")
            m = vtkutils.readMesh("ball.vtk")
            print("Read", m.GetNumberOfPolys(), "polygons")
            m = vtkutils.readMesh("ball.ply")
            print("Read", m.GetNumberOfPolys(), "polygons")
        except:
            print("Bad read")
            self.fail("readMesh failed")


    def test_readVTKVolume(self):
        print("Testing readVTKVolume")
        tetra = create_data.make_tetra(32)
        sitk.WriteImage(tetra, "tetra.vtk")
        try:
            vtkvol = vtkutils.readVTKVolume("tetra.vtk")
            print(type(vtkvol))
            print(vtkvol.GetDimensions())
        except:
            sitk.fail("readVTKVolume failed")

        try:
            os.remove("tetra.vtk")
        except:
            print("remove tetra.vtk failed")

if __name__ == "__main__":
    unittest.main()

