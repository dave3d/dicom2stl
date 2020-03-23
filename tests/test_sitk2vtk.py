#! /usr/bin/env python

import unittest
from utils import sitk2vtk
import vtk
import SimpleITK as sitk
import platform

class TestSITK2VTK(unittest.TestCase):

    def test_sitk2vtk(self):
        print("Testing sitk2vtk")
        img = sitk.GaussianSource(sitk.sitkUInt8, [102, 102, 102])

        if platform.system() == "Windows":
            invol = vtk.vtkImageData()
            invol.SetDimensions(10, 10, 10)
            vol = sitk2vtk.sitk2vtk(img, invol, True)
            print("Accessing VTK image")
            print(invol.GetScalarComponentAsFloat(5, 5, 5, 0))
        else:
            vol = sitk2vtk.sitk2vtk(img, None, True)
            print("Accessing VTK image")
            print(vol.GetScalarComponentAsFloat(5, 5, 5, 0))


if __name__ == "__main__":
    unittest.main()

