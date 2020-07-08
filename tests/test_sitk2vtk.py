#! /usr/bin/env python

import unittest
from utils import sitk2vtk
import vtk
import SimpleITK as sitk
import platform


class TestSITK2VTK(unittest.TestCase):

    def test_sitk2vtk(self):
        print("Testing sitk2vtk")
        dims = [102, 102, 102]
        img = sitk.GaussianSource(sitk.sitkUInt8, dims)

        vol = sitk2vtk.sitk2vtk(img, True)
        self.assertTupleEqual(vol.GetDimensions(), tuple(dims))
        print("Accessing VTK image")
        val = vol.GetScalarComponentAsFloat(5, 5, 5, 0)
        print(val)
        self.assertAlmostEqual(val, 3.0)


if __name__ == "__main__":
    unittest.main()
