#! /usr/bin/env python

import unittest
import os, shutil, zipfile
import vtk
import SimpleITK as sitk

from utils import dicomutils
from tests import create_data
from tests import write_series

class TestDicomUtils(unittest.TestCase):

    TMPDIR = "testtmp"
    SIZE = 32

    @classmethod
    def setUpClass(cls):
        print("\nBuildin\' it up!")
        cyl = create_data.make_cylinder(TestDicomUtils.SIZE, sitk.sitkUInt16)
        try:
            os.mkdir(TestDicomUtils.TMPDIR)
        except:
            print("Oopsie")
        write_series.write_series( cyl, TestDicomUtils.TMPDIR )

    @classmethod
    def tearDownClass(cls):
        print("\nTearin\' it down!")
        shutil.rmtree(TestDicomUtils.TMPDIR)

    def test_scanDirForDicom(self):
        print("\nTesting DicomUtils.scanDirForDicom")
        matches, dirs = dicomutils.scanDirForDicom(TestDicomUtils.TMPDIR)
        print(matches, dirs)
        self.assertEqual(len(matches), TestDicomUtils.SIZE)

    def test_getAllSeries(self):
        print("\nTesting DicomUtils.getAllSeries")
        seriessets = dicomutils.getAllSeries([TestDicomUtils.TMPDIR])
        print(seriessets)
        self.assertEqual(len(seriessets),1)
        series_id = seriessets[0][0]
        if series_id.startswith('1.2.826.0.1.3680043'):
           print("    Series looks good")
        else:
           self.fail("    Bad series: "+series_id)

    def test_getModality(self):
        print("\nTesting DicomUtils.getModality")
        img = sitk.Image(10,10,sitk.sitkUInt16)
        m1 = dicomutils.getModality(img)
        self.assertEqual(m1, "")
        img.SetMetaData("0008|0060", "dude")
        m2 = dicomutils.getModality(img)
        self.assertEqual(m2, "dude")

    def test_loadLargestSeries(self):
        print("\nTesting DicomUtils.loadLargestSeries")
        img, mod = dicomutils.loadLargestSeries(TestDicomUtils.TMPDIR)
        self.assertEqual(img.GetSize(), (TestDicomUtils.SIZE,TestDicomUtils.SIZE,TestDicomUtils.SIZE))
        self.assertEqual(mod, "CT")

    def test_loadZipDicom(self):
        print("\nTesting DicomUtils.loadZipDicom")
        zf = zipfile.ZipFile('tests/testzip.zip', 'w')
        for z in range(TestDicomUtils.SIZE):
            zf.write(TestDicomUtils.TMPDIR+'/'+str(z)+'.dcm')
        zf.close()
        img, mod = dicomutils.loadZipDicom('tests/testzip.zip', 'tests/ziptmp')
        print(img.GetSize())
        print(mod)
        os.unlink('tests/testzip.zip')
        shutil.rmtree('tests/ziptmp')



if __name__ == "__main__":
    unittest.main()

