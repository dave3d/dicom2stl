#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "simpleitkutilities>=0.3.0",
#   "SimpleITK>=2.5.3",
#   "vtk>=9.5.2",
# ]
# ///

"""Unit tests for SimpleITK utility functions."""

import unittest

import SimpleITK as sitk
import vtk
from SimpleITK.utilities.vtk import sitk2vtk


class TestSitkUtils(unittest.TestCase):
    """Test suite for SimpleITK utility functions."""

    def test_sitk2vtk(self):
        """Test converting SimpleITK to VTK with direction matrix."""
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
