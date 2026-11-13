#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "dicom2stl",
#   "SimpleITK>=2.5.3",
# ]
# ///

"""Unit tests for DICOM utility functions."""

import os
import shutil
import tempfile
import unittest
import zipfile
from unittest import mock

import SimpleITK as sitk
from tests import create_data
from tests import write_series
from dicom2stl.utils import dicomutils


class TestDicomUtils(unittest.TestCase):
    """Test suite for DICOM utility functions."""
    TMPDIR = "testtmp"
    SIZE = 32

    @classmethod
    def setUpClass(cls):
        print("\nBuildin' it up!")
        cyl = create_data.make_cylinder(TestDicomUtils.SIZE, sitk.sitkUInt16)
        try:
            os.mkdir(TestDicomUtils.TMPDIR)
        except OSError:
            print("Oopsie")
        write_series.write_series(cyl, TestDicomUtils.TMPDIR)

    @classmethod
    def tearDownClass(cls):
        print("\nTearin' it down!")
        shutil.rmtree(TestDicomUtils.TMPDIR)

    @staticmethod
    def copy_series(dest, suffix):
        """Copy the test series to dest, replacing the ".dcm" suffix."""
        for z in range(TestDicomUtils.SIZE):
            shutil.copy(
                os.path.join(TestDicomUtils.TMPDIR, str(z) + ".dcm"),
                os.path.join(dest, str(z) + suffix),
            )

    def test_testDicomFile(self):
        """Test recognizing a DICOM file by its header."""
        dcm = os.path.join(TestDicomUtils.TMPDIR, "0.dcm")
        self.assertTrue(dicomutils.testDicomFile(dcm))
        self.assertFalse(dicomutils.testDicomFile(__file__))
        self.assertFalse(dicomutils.testDicomFile(TestDicomUtils.TMPDIR))
        with mock.patch.object(
            dicomutils, "is_dicom", side_effect=PermissionError
        ):
            self.assertFalse(dicomutils.testDicomFile(dcm))

    def test_scanDirForDicom(self):
        """Test scanning directory for DICOM files."""
        matches, dirs = dicomutils.scanDirForDicom(TestDicomUtils.TMPDIR)
        print(matches, dirs)
        self.assertEqual(len(matches), TestDicomUtils.SIZE)

    def test_scanDirForDicom_without_suffix(self):
        """Test finding DICOM files that don't have the ".dcm" suffix."""
        for suffix in ["", ".IMA", ".DCM"]:
            with self.subTest(suffix=suffix):
                with tempfile.TemporaryDirectory() as tmpdir:
                    self.copy_series(tmpdir, suffix)
                    matches, dirs = dicomutils.scanDirForDicom(tmpdir)
                self.assertEqual(len(matches), TestDicomUtils.SIZE)
                self.assertEqual(dirs, [tmpdir])

    def test_scanDirForDicom_skips_other_files(self):
        """Test that files which are not DICOM images are left out."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.copy_series(tmpdir, "")
            os.mkdir(os.path.join(tmpdir, "viewer"))
            for name, data in [
                ("README", b"Not a DICOM file.\n"),
                ("EMPTY", b""),
                ("thumbnail.jpg", b"\xff\xd8\xff\xe0" + bytes(300)),
                ("DICOMDIR", bytes(128) + b"DICM"),
                (os.path.join("viewer", "viewer.cfg"), b"[viewer]\n"),
            ]:
                with open(os.path.join(tmpdir, name), "wb") as fp:
                    fp.write(data)
            matches, dirs = dicomutils.scanDirForDicom(tmpdir)
        slices = [
            os.path.join(tmpdir, str(z)) for z in range(TestDicomUtils.SIZE)
        ]
        self.assertEqual(sorted(matches), sorted(slices))
        self.assertEqual(dirs, [tmpdir])

    def test_getAllSeries(self):
        """Test getting all DICOM series from directories."""
        seriessets = dicomutils.getAllSeries([TestDicomUtils.TMPDIR])
        print(seriessets)
        self.assertEqual(len(seriessets), 1)
        series_id = seriessets[0][0]
        if series_id.startswith("1.2.826.0.1.3680043"):
            print("    Series looks good")
        else:
            self.fail("    Bad series: " + series_id)

    def test_getModality(self):
        """Test getting image modality from metadata."""
        img = sitk.Image(10, 10, sitk.sitkUInt16)
        m1 = dicomutils.getModality(img)
        self.assertEqual(m1, "")
        img.SetMetaData("0008|0060", "dude")
        m2 = dicomutils.getModality(img)
        self.assertEqual(m2, "dude")

    def test_loadLargestSeries(self):
        """Test loading the largest DICOM series from a directory."""
        img, mod = dicomutils.loadLargestSeries(TestDicomUtils.TMPDIR)
        self.assertEqual(
            img.GetSize(),
            (TestDicomUtils.SIZE, TestDicomUtils.SIZE, TestDicomUtils.SIZE),
        )
        self.assertEqual(mod, "CT")

    def test_loadZipDicom(self):
        """Test loading DICOM files from a ZIP archive."""
        with zipfile.ZipFile("tests/testzip.zip", "w") as zf:
            for z in range(TestDicomUtils.SIZE):
                zf.write(TestDicomUtils.TMPDIR + "/" + str(z) + ".dcm")
        img, mod = dicomutils.loadZipDicom("tests/testzip.zip", "tests/ziptmp")
        print(img.GetSize())
        print(mod)
        os.unlink("tests/testzip.zip")
        shutil.rmtree("tests/ziptmp")


if __name__ == "__main__":
    unittest.main()
