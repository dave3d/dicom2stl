#! /usr/bin/env python

import unittest
import math
from utils import vtk2sitk
import vtk
import SimpleITK as sitk

from tests import compare_stats


def printStats(stats):
    print("    Min:", stats[0])
    print("    Max:", stats[1])
    print("    Mean:", stats[2])
    print("    StdDev:", stats[3])


class TestVTK2SITK(unittest.TestCase):

    def test_vtk2sitk(self):

        source = vtk.vtkImageSinusoidSource()
        source.Update()

        img = source.GetOutput()
        print("\nVTK source image")
        print(type(img))
        print(img.GetScalarTypeAsString())
        print(img.GetDimensions())

        print("\nConverting VTK to SimpleITK")
        sitkimg = vtk2sitk.vtk2sitk(img, True)

        print("\nResulting SimpleITK Image")
        print(type(sitkimg))
        print(sitkimg.GetPixelIDTypeAsString())
        print(sitkimg.GetSize())

        self.assertIsInstance(sitkimg, sitk.Image)
        self.assertTupleEqual(img.GetDimensions(), sitkimg.GetSize())

        # Create a VTK image of pixel type short
        cast = vtk.vtkImageCast()

        cast.SetInputConnection(0, source.GetOutputPort())

        cast.SetOutputScalarTypeToShort()
        cast.Update()

        img2 = cast.GetOutput()
        print("\nVTK short image")
        print(type(img2))
        print(img2.GetScalarTypeAsString())
        print(img2.GetDimensions())

        # Convert the short image to SimpleITK
        print("\nConverting short VTK to SimpleITK")
        sitkimg2 = vtk2sitk.vtk2sitk(img2, True)
        print("\nSimpleITK short image")
        print(type(sitkimg2))
        print(sitkimg2.GetPixelIDTypeAsString())
        print(sitkimg2.GetSize())

        self.assertIsInstance(sitkimg2, sitk.Image)
        self.assertTupleEqual(img2.GetDimensions(), sitkimg2.GetSize())


        # compare the statistics of the VTK and SimpleITK images
        ok = compare_stats.compare_stats(sitkimg2, img2)
        if ok:
            print("Statistics comparison passed")
        else:
            self.fail("Statistics comparison failed")


if __name__ == "__main__":
    unittest.main()
