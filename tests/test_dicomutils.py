#! /usr/bin/env python

import unittest
import os, shutil
from utils import dicomutils
import vtk
import SimpleITK as sitk
from tests import create_data
from tests import write_series

class TestDicomUtils(unittest.TestCase):

    TMPDIR = "testtmp"

    def setUp(self):
        print("\nBuildin\' it up!")
        cyl = create_data.make_cylinder(32, sitk.sitkUInt16)
        try:
            os.mkdir(self.TMPDIR)
        except:
            print("Oopsie")
        write_series.write_series( cyl, self.TMPDIR )


    def tearDown(self):
        print("\nTearin\' it down!")
        shutil.rmtree(self.TMPDIR)

    def test_dicomutils(self):

        print("\nTesting DicomUtils.scanDirForDicom")
        matches, dirs = dicomutils.scanDirForDicom(self.TMPDIR)
        print(matches, dirs)
        self.assertEqual(len(matches), 32)

        print("\nTesting DicomUtils.getAllSeries")
        seriessets = dicomutils.getAllSeries([self.TMPDIR])
        print(seriessets)
        self.assertEqual(len(seriessets),1)
        series_id = seriessets[0][0]
        if series_id.startswith('1.2.826.0.1.3680043'):
           print("    Series looks good")
        else:
           self.fail("    Bad series: "+series_id)

if __name__ == "__main__":
    unittest.main()

