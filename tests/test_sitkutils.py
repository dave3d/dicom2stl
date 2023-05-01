#! /usr/bin/env python

import unittest
from SimpleITK.utilities.vtk import *
import vtk
import SimpleITK as sitk
import platform


class TestSitkUtils(unittest.TestCase):
    def test_sitk2vtk(self):
        print("Testing SimpleITK Utilities")
        dims = [102, 102, 102]
        img = sitk.GaussianSource(sitk.sitkUInt8, dims)
        direction = [0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0]
        img.SetDirection(direction)

        vol = sitk2vtk(img)
        self.assertTupleEqual(vol.GetDimensions(), tuple(dims))
        print("\nAccessing VTK image")
        val = vol.GetScalarComponentAsFloat(5, 5, 5, 0)
        print(val)
        self.assertAlmostEqual(val, 3.0)

        if vtk.vtkVersion.GetVTKMajorVersion() >= 9:
            print("\nDirection matrix")
            print(vol.GetDirectionMatrix())
        else:
            print("VTK version < 9.  No direction matrix")


if __name__ == "__main__":
    unittest.main()
