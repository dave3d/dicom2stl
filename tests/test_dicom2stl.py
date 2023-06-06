import unittest
import os

import SimpleITK as sitk
import parseargs
import dicom2stl

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
        print("\nDicom2stl test")
        print("cwd:", os.getcwd())

        parser = parseargs.createParser()
        args = parser.parse_args(
            ["-i", "100", "-o", "testout.stl", "tetra-test.nii.gz"]
        )

        print("\ndicom2stl arguments")
        print(args)

        try:
            dicom2stl.dicom2stl(args)
        except BaseException:
            self.fail("dicom2stl: exception thrown")

        if not os.path.exists("testout.stl"):
            self.fail("dicom2stl: no output file")


if __name__ == "__main__":
    unittest.main()
