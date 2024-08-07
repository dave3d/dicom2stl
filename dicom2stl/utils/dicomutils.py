#! /usr/bin/env python

"""
Function to load the largest Dicom series in a directory.

It scans the directory recursively search for files with the ".dcm"
suffix.  Note that DICOM fails don't always have that suffix.  In
that case this function will fail.

Written by David T. Chen from the National Institute of Allergy
and Infectious Diseases, dchen@mail.nih.gov.
It is covered by the Apache License, Version 2.0:
http://www.apache.org/licenses/LICENSE-2.0
"""


from __future__ import print_function
import sys
import os
import fnmatch
import zipfile
import SimpleITK as sitk

from pydicom.filereader import read_file_meta_info
from pydicom.errors import InvalidDicomError


def testDicomFile(file_path):
    """Test if given file is in DICOM format."""
    try:
        read_file_meta_info(file_path)
        return True
    except InvalidDicomError:
        return False


def scanDirForDicom(dicomdir):
    """Scan directory for dicom series."""
    matches = []
    found_dirs = []
    try:
        for walk_output in os.walk(dicomdir):
            root = walk_output[0]
            filenames = walk_output[2]
            for filename in fnmatch.filter(filenames, "*.dcm"):
                matches.append(os.path.join(root, filename))
                if root not in found_dirs:
                    found_dirs.append(root)
    except IOError as e:
        print("Error in scanDirForDicom: ", e)
        print("dicomdir = ", dicomdir)

    return (matches, found_dirs)


def getAllSeries(target_dirs):
    """Get all the Dicom series in a set of directories."""
    isr = sitk.ImageSeriesReader()
    found_series = []
    for d in target_dirs:
        series = isr.GetGDCMSeriesIDs(d)
        for s in series:
            found_files = isr.GetGDCMSeriesFileNames(d, s)
            print(s, d, len(found_files))
            found_series.append([s, d, found_files])
    return found_series


def getModality(img):
    """Get an image's modality, as stored in the Dicom meta data."""
    modality = ""
    if (sitk.Version.MinorVersion() > 8) or (sitk.Version.MajorVersion() > 0):
        try:
            modality = img.GetMetaData("0008|0060")
        except RuntimeError:
            modality = ""
    return modality


def loadLargestSeries(dicomdir):
    """
    Load the largest Dicom series it finds in a recursive scan of
    a directory.

    Largest means has the most slices.  It also returns the modality
    of the series.
    """

    files, dirs = scanDirForDicom(dicomdir)

    if (len(files) == 0) or (len(dirs) == 0):
        print("Error in loadLargestSeries.  No files found.")
        print("dicomdir = ", dicomdir)
        return None
    seriessets = getAllSeries(dirs)
    maxsize = 0
    maxindex = -1

    count = 0
    for ss in seriessets:
        size = len(ss[2])
        if size > maxsize:
            maxsize = size
            maxindex = count
        count = count + 1
    if maxindex < 0:
        print("Error:  no series found")
        return None
    isr = sitk.ImageSeriesReader()
    ss = seriessets[maxindex]
    files = ss[2]
    isr.SetFileNames(files)
    print("\nLoading series", ss[0], "in directory", ss[1])
    img = isr.Execute()

    firstslice = sitk.ReadImage(files[0])
    modality = getModality(firstslice)

    return img, modality


def loadZipDicom(name, tempDir):
    """Unzip a zipfile of dicom images into a temp directory, then
    load the series that has the most slices.
    """

    print("Reading Dicom zip file:", name)
    print("tempDir = ", tempDir)
    with zipfile.ZipFile(name, "r") as myzip:

        try:
            myzip.extractall(tempDir)
        except RuntimeError:
            print("Zip extract failed")

    return loadLargestSeries(tempDir)


#
#   Main (test code)
#

if __name__ == "__main__":
    print("")
    print("dicomutils.py")
    print(sys.argv[1])

    #    img = loadLargestSeries(sys.argv[1])
    #    print (img)
    #    sys.exit(0)

    dcm_files, dcm_dirs = scanDirForDicom(sys.argv[1])
    print("")
    print("files")
    print(dcm_files)
    print("")
    print("dirs")
    print(dcm_dirs)

    print("series")
    series_found = getAllSeries(dcm_dirs)
    for sf in series_found:
        print(sf[0], " ", sf[1])
        print(len(sf[2]))
        print("")
