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
import shutil
import time
import zipfile
import vtk
import re
import SimpleITK as sitk

import parseargs

from glob import glob

from utils import sitk2vtk
from utils import dicomutils
from utils import vtkutils

# Global variables
#

zipFlag = False
dirFlag = False

shrinkFlag = True
thesholds = []
shrinkFlag = True
connectivityFilter = False
anisotropicSmoothing = False
medianFilter = False
rotFlag = False

args = parseargs.parseargs()

isovalue = args.isovalue

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
        if y.startswith("rotat"):
            rotFlag = val

print("")
tempDir = args.temp
if not tempDir:
    print("Temp dir: Not specified, a temp dir will be created at current path")
else:
    print("Temp dir: ", tempDir)

tissueType = args.tissue
if tissueType:
    # Convert tissue type name to threshold values
    print("Tissue type: ", tissueType)
    if tissueType.find("bone") > -1:
        thresholds = [200., 800., 1300., 1500.]
    elif tissueType.find("skin") > -1:
        thresholds = [-200., 0., 500., 1500.]
    elif tissueType.find("soft") > -1:
        thresholds = [-15., 30., 58., 100.]
        medianFilter = True
    elif tissueType.find("fat") > -1:
        thresholds = [-122., -112., -96., -70.]
        medianFilter = True

if args.double_threshold:
    words = args.double_threshold.split(';')
    thresholds = []
    for x in words:
        thresholds.append(float(x))
    # check that there are 4 threshold values.
    print("Thresholds: ", thresholds)
    if len(thresholds) != 4:
        print("Error: Thresholds is not of len 4.", thresholds)
        sys.exit(3)
else:
    print("Isovalue = ", isovalue)

fname = args.filenames

# Parse wildcards
# sum() flatten nested list
fname = sum([glob(f) for f in fname], [])

if len(fname) == 0:
    print("Error: no valid input given.")
    sys.exit(4)

if zipfile.is_zipfile(fname[0]):
    zipFlag = True

if os.path.isdir(fname[0]):
    dirFlag = True
else:
    if len(fname) > 1:
        print("File names: ", fname[0], fname[1], "...",
              fname[len(fname) - 1], "\n")
    else:
        print("File names: ", fname, "\n")


if args.debug:
    print("SimpleITK version: ", sitk.Version.VersionString())
    print("SimpleITK: ", sitk, "\n")

img = sitk.Image(100, 100, 100, sitk.sitkUInt8)
dcmnames = []
metasrc = img


#  Load our Dicom data
#
if zipFlag:
    # Case for a zip file of images
    if args.verbose:
        print("zip")
    if not tempDir:
        with tempfile.TemporaryDirectory() as defaultTempDir:
            img, modality = dicomutils.loadZipDicom(fname[0], defaultTempDir)
    else:
        img, modality = dicomutils.loadZipDicom(fname[0], tempDir)


else:
    if dirFlag:
        if args.verbose:
            print("directory")
        img, modality = dicomutils.loadLargestSeries(fname[0])

    else:
        # Case for a single volume image
        if len(fname) == 1:
            if args.verbose:
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
            
            if args.verbose:
                if args.verbose > 1:
                    print("Reading images: ", fname)
                else:
                    print("Reading images: ",
                          fname[0], fname[1], "...", fname[len(fname) - 1])
            isr = sitk.ImageSeriesReader()
            isr.SetFileNames(fname)
            img = isr.Execute()
            firstslice = sitk.ReadImage(fname[0])
            modality = dicomutils.getModality(firstslice)

if args.ctonly and ((sitk.Version.MinorVersion() > 8)
                    or (sitk.Version.MajorVersion() > 0)):
    # Check the metadata for CT image type.  Note that this only works with
    # SimpleITK version 0.8.0 or later.  For earlier versions there is no
    # GetMetaDataKeys method
    if modality.find("CT") == -1:
        print("Imaging modality is not CT.  Exiting.")
        sys.exit(1)


# vtkname =  tempDir+"/vol0.vtk"
# sitk.WriteImage( img, vtkname )

def roundThousand(x):
    y = int(1000.0 * x + 0.5)
    return str(float(y) * .001)


def elapsedTime(start_time):
    dt = roundThousand(time.perf_counter() - start_time)
    print("    ", dt, "seconds")


# Write out the metadata text file
#
if args.meta:
    FP = open(args.meta, "w")
    size = img.GetSize()
    spacing = img.GetSpacing()
    FP.write('xdimension ' + str(size[0]) + '\n')
    FP.write('ydimension ' + str(size[1]) + '\n')
    FP.write('zdimension ' + str(size[2]) + '\n')
    FP.write('xspacing ' + roundThousand(spacing[0]) + '\n')
    FP.write('yspacing ' + roundThousand(spacing[1]) + '\n')
    FP.write('zspacing ' + roundThousand(spacing[2]) + '\n')
    FP.close()

#
# shrink the volume to 256 cubed
if shrinkFlag:
    sfactor = []
    size = img.GetSize()
    total = 0
    for s in size:
        x = int(math.ceil(s / 256.0))
        sfactor.append(x)
        total = total + x

    if total > 3:
        # if total==3, no shrink happens
        t = time.perf_counter()
        print("Shrink factors: ", sfactor)
        img = sitk.Shrink(img, sfactor)
        newsize = img.GetSize()
        print(size, "->", newsize)
        elapsedTime(t)

gc.collect()

# Apply anisotropic smoothing to the volume image.  That's a smoothing filter
# that preserves edges.
#
if anisotropicSmoothing:
    print("Anisotropic Smoothing")
    t = time.process_time()
    pixelType = img.GetPixelID()
    img = sitk.Cast(img, sitk.sitkFloat32)
    img = sitk.CurvatureAnisotropicDiffusion(img, .03)
    img = sitk.Cast(img, pixelType)
    elapsedTime(t)
    gc.collect()

# Apply the double threshold filter to the volume
#
if args.double_threshold:
    print("Double Threshold")
    t = time.process_time()
    img = sitk.DoubleThreshold(
        img, thresholds[0], thresholds[1], thresholds[2], thresholds[3],
        255, 0)
    isovalue = 64.0
    elapsedTime(t)
    gc.collect()

# Apply a 3x3x1 median filter.  I only use 1 in the Z direction so it's not so
# slow.
#
if medianFilter:
    print("Median filter")
    t = time.process_time()
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

if args.verbose:
    print("\nImage for isocontouring")
    print(img.GetSize())
    print(img.GetPixelIDTypeAsString())
    print(img.GetSpacing())
    print(img.GetOrigin())
    if args.verbose > 1:
        print(img)
    print("")

# vtkname =  tempDir+"/vol.vtk"
# sitk.WriteImage( img, vtkname )


vtkimg = sitk2vtk.sitk2vtk(img)

img = None
gc.collect()

if args.debug:
    print("\nVTK version: ", vtk.vtkVersion.GetVTKVersion())
    print("VTK: ", vtk, "\n")

if args.debug:
    print("Extracting surface")
mesh = vtkutils.extractSurface(vtkimg, isovalue)
vtkimg = None
gc.collect()
if args.debug:
    print("Cleaning mesh")
mesh2 = vtkutils.cleanMesh(mesh, connectivityFilter)
mesh = None
gc.collect()
if args.debug:
    print("Smoothing mesh", args.smooth, "iterations")
mesh3 = vtkutils.smoothMesh(mesh2, args.smooth)
mesh2 = None
gc.collect()
if args.debug:
    print("Simplifying mesh")
mesh4 = vtkutils.reduceMesh(mesh3, args.reduce)
mesh3 = None
gc.collect()

axis_map = {'X': 0, 'Y': 1, 'Z': 2}
rotAxis = axis_map[args.rotaxis]
if args.rotangle != 0.0:
    mesh5 = vtkutils.rotateMesh(mesh4, rotAxis, args.rotangle)
else:
    mesh5 = mesh4
vtkutils.writeMesh(mesh5, args.output)
mesh4 = None
gc.collect()

# remove the temp directory
if args.clean:
    # shutil.rmtree(tempDir)
    # with context manager the temp dir would be deleted any way
    pass

print("")
