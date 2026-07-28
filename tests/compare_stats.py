#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "SimpleITK>=2.5.3",
#   "vtk>=9.5.2",
# ]
# ///

"""Statistics comparison utilities for DICOM to STL conversion tests."""

import SimpleITK as sitk
import vtk


def printStats(stats):
    """Print image statistics in a formatted manner.

    Args:
        stats: List of [min, max, mean, stddev] statistics
    """
    print("    Max:", stats[1])
    print("    Mean:", stats[2])
    print("    StdDev:", stats[3])


def compare_stats(sitkimg, vtkimg):
    """Compare image statistics between SimpleITK and VTK images.

    Args:
        sitkimg: SimpleITK image to compare
        vtkimg: VTK image to compare

    Returns:
        True if statistics match within tolerance, False otherwise
    """

    # Compute the VTK image histogram statistics
    histo = vtk.vtkImageHistogramStatistics()
    histo.SetInputData(vtkimg)
    histo.Update()
    print(histo.GetStandardDeviation())

    vtkstats = [
        histo.GetMinimum(),
        histo.GetMaximum(),
        histo.GetMean(),
        histo.GetStandardDeviation(),
    ]

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
        stats.GetSigma(),
    ]

    print("\nSimpleITK image stats")
    printStats(sitkstats)

    # compare the statistics of the VTK and SimpleITK images
    ok = True
    for v, s in zip(vtkstats, sitkstats):
        x = v - s
        if v != 0.0:
            y = abs(x / v)
        else:
            y = abs(x)

        if y > 0.0001:
            print("Bad!", v, s, "\terror =", y)
            ok = False
    return ok


if __name__ == "__main__":

    dims = [10, 10, 10]
    val = 0

    img = sitk.Image(dims, sitk.sitkUInt8)
    img = img + val

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
