#! /usr/bin/env python

import unittest
from utils import vtkutils
import vtk
import SimpleITK as sitk
import platform

class TestVTKUtils(unittest.TestCase):

    BALL = None

    @classmethod
    def setUpClass(cls):
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

if __name__ == "__main__":
    unittest.main()

