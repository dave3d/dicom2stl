#! /usr/bin/env python

import unittest

import SimpleITK as sitk


import create_data

class TestDicom2STL(unittest.TestCase):

    def test_dicom2stl(self):
        img = create_data.make_tetra()
        sitk.WriteImage(img, "tetra.nii.gz")


if __name__ == "__main__":
    unittest.main()
