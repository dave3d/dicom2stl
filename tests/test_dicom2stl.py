"""Unit tests for DICOM to STL conversion functionality."""

import unittest
import os
import tempfile
import zipfile

import SimpleITK as sitk
from dicom2stl.utils import parseargs
from dicom2stl.Dicom2STL import Dicom2STL, loadVolume

from tests import create_data
from tests import write_series


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


class TestLoadVolume(unittest.TestCase):
    """Test suite for loading a DICOM series from a directory or zip file."""

    def test_dicom_without_suffix(self):
        """Test loading DICOM files that don't have the ".dcm" suffix."""
        size = 16
        with tempfile.TemporaryDirectory() as tmpdir:
            dcmdir = os.path.join(tmpdir, "series")
            os.mkdir(dcmdir)
            cyl = create_data.make_cylinder(size, pixel_type=sitk.sitkUInt16)
            write_series.write_series(cyl, dcmdir)
            for name in os.listdir(dcmdir):
                path = os.path.join(dcmdir, name)
                os.rename(path, os.path.splitext(path)[0])
            zipname = os.path.join(tmpdir, "series.zip")
            with zipfile.ZipFile(zipname, "w") as zf:
                for name in os.listdir(dcmdir):
                    zf.write(os.path.join(dcmdir, name), name)

            for name in [dcmdir, zipname]:
                with self.subTest(name=name):
                    img, modality = loadVolume([name])
                    self.assertEqual(img.GetSize(), (size, size, size))
                    self.assertEqual(modality, "CT")

    def test_no_dicom_series(self):
        """Test the error exit when the input has no DICOM series."""
        with tempfile.TemporaryDirectory() as tmpdir:
            emptydir = os.path.join(tmpdir, "empty")
            os.mkdir(emptydir)
            zipname = os.path.join(tmpdir, "nodicom.zip")
            with zipfile.ZipFile(zipname, "w") as zf:
                zf.writestr("README", "No images here.\n")

            for name in [emptydir, zipname]:
                with self.subTest(name=name):
                    with self.assertRaises(SystemExit) as cm:
                        loadVolume([name])
                    self.assertEqual(cm.exception.code, 5)


if __name__ == "__main__":
    unittest.main()
