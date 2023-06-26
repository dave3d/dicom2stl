#! /usr/bin/env python

import unittest
import vtk
import SimpleITK as sitk
import SimpleITK.utilities as sitkutils
import platform


class TestSITK2VTK(unittest.TestCase):
    def test_sitk2vtk(self):
        print("Testing sitk2vtk")
        dims = [102, 102, 102]
        img = sitk.GaussianSource(sitk.sitkUInt8, dims)
        direction = [0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0]
        img.SetDirection(direction)

        vol = sitkutils.sitk2vtk(img)
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
