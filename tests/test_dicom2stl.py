import unittest
import subprocess
import os

import SimpleITK as sitk

from tests import create_data


class TestDicom2STL(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        print("Setting up dicom2stl tests")
        img = create_data.make_tetra()
        sitk.WriteImage(img, "tetra-test.nii.gz")

    @classmethod
    def tearDownClass(cls):
        print("Tearing down dicom2stl tests")
        os.remove("tetra-test.nii.gz")
        os.remove("testout.stl")

    def test_dicom2stl(self):
        print("Dicom2stl test")
        print(os.getcwd())
        runresult = subprocess.run(['python', 'dicom2stl.py', '-i', '100', '-o',
                                    'testout.stl', 'tetra-test.nii.gz'])
        print(runresult.returncode)
        if runresult.returncode:
            self.fail("dicom2stl process returned bad code")
        if not os.path.exists("testout.stl"):
            self.fail("dicom2stl: no output file")


if __name__ == "__main__":
    unittest.main()
