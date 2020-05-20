#! /usr/bin/env python

import math
import vtk
import SimpleITK as sitk


def printStats(stats):
    print("    Min:", stats[0])
    print("    Max:", stats[1])
    print("    Mean:", stats[2])
    print("    StdDev:", stats[3])


def compare_stats(sitkimg, vtkimg):
    """ Compare the statistics of a SimpleITK image and a VTK image. """

    # Compute the VTK image histogram statistics
    histo = vtk.vtkImageHistogramStatistics()
    histo.SetInputData(vtkimg)
    histo.Update()
    print(histo.GetStandardDeviation())

    vtkstats = [
        histo.GetMinimum(),
        histo.GetMaximum(),
        histo.GetMean(),
        histo.GetStandardDeviation() ]

    print("\nvtk median = ", histo.GetMedian())

    print("\nVTK source image stats")
    printStats(vtkstats)

    # Compute the SimpleITK image statistics
    stats = sitk.StatisticsImageFilter()
    stats.Execute(sitkimg)

    sitkstats = [
        stats.GetMinimum(),
        stats.GetMaximum(),
        stats.GetMean(),
        stats.GetSigma() ]

    print("\nSimpleITK image stats")
    printStats(sitkstats)


    # compare the statistics of the VTK and SimpleITK images
    ok = True
    for v, s in zip(vtkstats, sitkstats):
        x = v-s
        y = math.sqrt(x*x)
        if (y>.0001):
            print("Bad!", v, s)
            ok=False
    return ok


if __name__ == "__main__":

    dims = [10,10,10]
    val = 0

    img = sitk.Image(dims,sitk.sitkUInt8)
    img = img+val

    img2 = vtk.vtkImageData()
    img2.SetDimensions(dims)

    img2.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)
    for z in range(dims[2]):
        for y in range(dims[1]):
            for x in range(dims[0]):
                img2.SetScalarComponentFromFloat(x, y, z, 0, val)

    ret = compare_stats(img, img2)

    if ret:
        print("PASS")
    else:
        print("FAIL")


