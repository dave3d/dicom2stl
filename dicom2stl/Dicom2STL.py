#! /usr/bin/env python

"""
Script to take a Dicom series and generate an STL surface mesh.

Written by David T. Chen from the National Institute of Allergy
and Infectious Diseases, dchen@mail.nih.gov.
It is covered by the Apache License, Version 2.0:
http://www.apache.org/licenses/LICENSE-2.0

Note: if you run this script with the individual Dicom slices provided on the
command line, they might not be ordered in the correct order.  You are better
off providing a zip file or a directory.  Dicom slices are not necessarily
ordered the same alphabetically as they are physically.
"""

from __future__ import print_function

import gc
import math
import os
import sys
import tempfile
import time
import zipfile
import re
from glob import glob
import vtk
import SimpleITK as sitk

from SimpleITK.utilities.vtk import sitk2vtk


from dicom2stl.utils import dicomutils
from dicom2stl.utils import vtkutils
from dicom2stl.utils import parseargs


def roundThousand(x):
    """Round to the nearest thousandth"""
    y = int(1000.0 * x + 0.5)
    return str(float(y) * 0.001)


def elapsedTime(start_time):
    """Print the elapsed time"""
    dt = time.perf_counter() - start_time
    print(f"    {dt:4.3f} seconds")


def loadVolume(fname, tempDir=None, verbose=0):
    """Load the volume image from a zip file, a directory of Dicom files,
    or a single volume image.  Return the SimpleITK image and the modality."""
    modality = None
    zipFlag = False
    dirFlag = False

    # Parse wildcards
    # sum() flatten nested list
    fname = sum([glob(f) for f in fname], [])

    if len(fname) == 0:
        print("Error: no valid input given.")
        sys.exit(4)

    zipFlag = zipfile.is_zipfile(fname[0])

    dirFlag = os.path.isdir(fname[0])

    img = sitk.Image(100, 100, 100, sitk.sitkUInt8)

    #  Load our Dicom data
    #
    if zipFlag:
        # Case for a zip file of images
        if not tempDir:
            with tempfile.TemporaryDirectory() as defaultTempDir:
                img, modality = dicomutils.loadZipDicom(fname[0], defaultTempDir)
        else:
            img, modality = dicomutils.loadZipDicom(fname[0], tempDir)

    else:
        if dirFlag:
            img, modality = dicomutils.loadLargestSeries(fname[0])

        else:
            # Case for a single volume image
            if len(fname) == 1:
                if verbose:
                    print("Reading volume: ", fname[0])
                img = sitk.ReadImage(fname[0])
                modality = dicomutils.getModality(img)

            else:
                # Case for a series of image files
                # For files named like IM1, IM2, .. IM10
                # They would be ordered by default as IM1, IM10, IM2, ...
                # sort the fname list in correct serial number order
                RE_NUMBERS = re.compile(r"\d+")

                def extract_int(file_path):
                    file_name = os.path.basename(file_path)
                    return int(RE_NUMBERS.findall(file_name)[0])

                fname = sorted(fname, key=extract_int)

                if verbose:
                    if verbose > 1:
                        print("Reading images: ", fname)
                    else:
                        print(
                            "Reading images: ",
                            fname[0],
                            fname[1],
                            "...",
                            fname[len(fname) - 1],
                        )
                isr = sitk.ImageSeriesReader()
                isr.SetFileNames(fname)
                img = isr.Execute()
                firstslice = sitk.ReadImage(fname[0])
                modality = dicomutils.getModality(firstslice)

    return img, modality


def writeMetadataFile(img, metaName):
    """Write out the metadata to a text file"""
    with open(metaName, "wb") as fp:
        size = img.GetSize()
        spacing = img.GetSpacing()
        fp.write(b"xdimension " + str(size[0]).encode() + b"\n")
        fp.write(b"ydimension " + str(size[1]).encode() + b"\n")
        fp.write(b"zdimension " + str(size[2]).encode() + b"\n")
        fp.write(b"xspacing " + roundThousand(spacing[0]).encode() + b"\n")
        fp.write(b"yspacing " + roundThousand(spacing[1]).encode() + b"\n")
        fp.write(b"zspacing " + roundThousand(spacing[2]).encode() + b"\n")


def shrinkVolume(input_image, newsize):
    """Shrink the volume to a new size"""
    size = input_image.GetSize()
    total = 0
    sfactor = []
    for s in size:
        x = int(math.ceil(s / float(newsize)))
        sfactor.append(x)
        total = total + x

    if total > 3:
        # if total==3, no shrink happens
        t = time.perf_counter()
        print("Shrink factors: ", sfactor)
        img = sitk.Shrink(input_image, sfactor)
        newsize = img.GetSize()
        print(size, "->", newsize)
        elapsedTime(t)
        return img

    return input_image

def volumeProcessingPipeline(
    img, shrinkFlag=True, anisotropicSmoothing=False, thresholds=None, medianFilter=False
):
    """Apply a series of filters to the volume image"""
    #
    # shrink the volume to 256 cubed
    if shrinkFlag:
        shrinkVolume(img, 256)

    gc.collect()

    # Apply anisotropic smoothing to the volume image.  That's a smoothing
    # filter that preserves edges.
    #
    if anisotropicSmoothing:
        print("Anisotropic Smoothing")
        t = time.perf_counter()
        pixelType = img.GetPixelID()
        img = sitk.Cast(img, sitk.sitkFloat32)
        img = sitk.CurvatureAnisotropicDiffusion(img, 0.03)
        img = sitk.Cast(img, pixelType)
        elapsedTime(t)
        gc.collect()

    # Apply the double threshold filter to the volume
    #
    if isinstance(thresholds, list) and len(thresholds)==4:
        print("Double Threshold: ", thresholds)
        t = time.perf_counter()
        img = sitk.DoubleThreshold(
            img, thresholds[0], thresholds[1], thresholds[2], thresholds[3], 255, 0
        )
        elapsedTime(t)
        gc.collect()

    # Apply a 3x3x1 median filter.  I only use 1 in the Z direction so it's
    # not so slow.
    #
    if medianFilter:
        print("Median filter")
        t = time.perf_counter()
        img = sitk.Median(img, [3, 3, 1])
        elapsedTime(t)
        gc.collect()

    #
    # Get the minimum image intensity for padding the image
    #
    stats = sitk.StatisticsImageFilter()
    stats.Execute(img)
    minVal = stats.GetMinimum()

    # Pad black to the boundaries of the image
    #
    pad = [5, 5, 5]
    img = sitk.ConstantPad(img, pad, pad, minVal)
    gc.collect()

    return img


def meshProcessingPipeline(
    mesh,
    connectivityFilter=False,
    smallFactor=0.05,
    smoothN=25,
    reduceFactor=0.9,
    rotation=["X", 0.0],
    debug=False,
):
    """Apply a series of filters to the mesh"""
    if debug:
        print("Cleaning mesh")
    mesh2 = vtkutils.cleanMesh(mesh, connectivityFilter)
    mesh = None
    gc.collect()

    if debug:
        print(f"Cleaning small parts ratio{smallFactor}")
    mesh_cleaned_parts = vtkutils.removeSmallObjects(mesh2, smallFactor)
    mesh2 = None
    gc.collect()

    if debug:
        print("Smoothing mesh", smoothN, "iterations")
    mesh3 = vtkutils.smoothMesh(mesh_cleaned_parts, smoothN)
    mesh_cleaned_parts = None
    gc.collect()

    if debug:
        print("Simplifying mesh")
    mesh4 = vtkutils.reduceMesh(mesh3, reduceFactor)
    mesh3 = None
    gc.collect()

    print(rotation)
    axis_map = {"X": 0, "Y": 1, "Z": 2}
    try:
        rotAxis = axis_map[rotation[0]]
        if rotation[1] != 0.0:
            mesh5 = vtkutils.rotateMesh(mesh4, rotAxis, rotation[1])
        else:
            mesh5 = mesh4
    except RuntimeError:
        mesh5 = mesh4
    mesh4 = None
    gc.collect()

    return mesh5


def getTissueThresholds(tissueType):
    """Get the double threshold values for a given tissue type."""
    thresholds = []
    medianFilter = False

    # Convert tissue type name to threshold values
    print("Tissue type: ", tissueType)
    if tissueType.find("bone") > -1:
        thresholds = [200.0, 800.0, 1300.0, 1500.0]
    elif tissueType.find("skin") > -1:
        thresholds = [-200.0, 0.0, 500.0, 1500.0]
    elif tissueType.find("soft") > -1:
        thresholds = [-15.0, 30.0, 58.0, 100.0]
        medianFilter = True
    elif tissueType.find("fat") > -1:
        thresholds = [-122.0, -112.0, -96.0, -70.0]
        medianFilter = True
    else:
        thresholds = None

    return thresholds, medianFilter


def Dicom2STL(args):
    """The primary dicom2stl function"""
    # Global variables
    #
    thresholds = None
    shrinkFlag = True
    connectivityFilter = False
    anisotropicSmoothing = False
    medianFilter = False

    # Handle enable/disable filters

    if args.filters:
        for x in args.filters:
            val = True
            y = x
            if x[:2] == "no":
                val = False
                y = x[2:]
            if y.startswith("shrink"):
                shrinkFlag = val
            if y.startswith("aniso"):
                anisotropicSmoothing = val
            if y.startswith("median"):
                medianFilter = val
            if y.startswith("large"):
                connectivityFilter = val

    print("")
    if args.temp is None:
        args.temp = tempfile.mkdtemp()
    print("Temp dir: ", args.temp)

    if args.tissue:
        thresholds, medianFilter = getTissueThresholds(args.tissue)

    if args.double_threshold:
        words = args.double_threshold.split(";")
        thresholds = []
        for x in words:
            thresholds.append(float(x))
        # check that there are 4 threshold values.
        print("Thresholds: ", thresholds)
        if len(thresholds) != 4:
            print("Error: Thresholds is not of len 4.", thresholds)
            sys.exit(3)
    else:
        print("Isovalue = ", args.isovalue)

    if args.debug:
        print("SimpleITK version: ", sitk.Version.VersionString())
        print("SimpleITK: ", sitk, "\n")

    #
    # Load the volume image
    img, modality = loadVolume(args.filenames, args.temp, args.verbose)

    if args.ctonly:
        if modality.find("CT") == -1:
            print("Imaging modality is not CT.  Exiting.")
            sys.exit(1)

    # Write out the metadata text file
    if args.meta:
        writeMetadataFile(img, args.meta)

    #
    # Filter the volume image
    img = volumeProcessingPipeline(
        img, shrinkFlag, anisotropicSmoothing, thresholds, medianFilter
    )

    if isinstance(thresholds, list) and len(thresholds) == 4:
        args.isovalue = 64.0

    if args.verbose:
        print("\nImage for isocontouring")
        print(img.GetSize())
        print(img.GetPixelIDTypeAsString())
        print(img.GetSpacing())
        print(img.GetOrigin())
        if args.verbose > 1:
            print(img)
        print("")

    # Convert the SimpleITK image to a VTK image
    vtkimg = sitk2vtk(img)

    # Delete the SimpleITK image, free its memory
    img = None
    gc.collect()

    if args.debug:
        print("\nVTK version: ", vtk.vtkVersion.GetVTKVersion())
        print("VTK: ", vtk, "\n")

    # Extract the iso-surface
    if args.debug:
        print("Extracting surface")
    mesh = vtkutils.extractSurface(vtkimg, args.isovalue)

    # Delete the VTK image, free its memory
    vtkimg = None
    gc.collect()

    # Filter the output mesh
    mesh = meshProcessingPipeline(
        mesh,
        connectivityFilter,
        args.small,
        args.smooth,
        args.reduce,
        [args.rotaxis, args.rotangle],
        args.debug,
    )

    # We done!  Write out the results
    vtkutils.writeMesh(mesh, args.output)

    # remove the temp directory
    if args.clean:
        # shutil.rmtree(args.temp)
        # with context manager the temp dir would be deleted any way
        pass

    print("")


def main():
    """Main function"""
    args = parseargs.parseargs()
    Dicom2STL(args)


if __name__ == "__main__":
    main()
