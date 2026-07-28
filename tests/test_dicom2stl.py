"""Unit tests for DICOM to STL conversion functionality."""

import unittest
import os

import SimpleITK as sitk
from dicom2stl.utils import parseargs
from dicom2stl.Dicom2STL import Dicom2STL

from tests import create_data


class TestDicom2STL(unittest.TestCase):
    """Test suite for Dicom2STL conversion."""

    @classmethod
    def setUpClass(cls):
        print("Setting up dicom2stl tests")
        img = create_data.make_tetra()
        sitk.WriteImage(img, "tetra-test.nii.gz")

    @classmethod
    def tearDownClass(cls):
        print("Tearing down dicom2stl tests")
        os.remove("tetra-test.nii.gz")
        os.remove("testout.stl")

    def test_dicom2stl(self):
        """Test DICOM to STL conversion with standard parameters."""
        print("cwd:", os.getcwd())

        parser = parseargs.createParser()
        args = parser.parse_args(
            ["-i", "100", "-o", "testout.stl", "tetra-test.nii.gz"]
        )

        print("\ndicom2stl arguments")
        print(args)

        try:
            Dicom2STL(args)
        except (RuntimeError, ValueError) as e:
            self.fail(f"dicom2stl: exception thrown: {e}")

        if not os.path.exists("testout.stl"):
            self.fail("dicom2stl: no output file")


if __name__ == "__main__":
    unittest.main()
