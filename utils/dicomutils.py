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


def scanDirForDicom(dicomdir):
    matches = []
    dirs = []
    for root, dirnames, filenames in os.walk(dicomdir):
        for filename in fnmatch.filter(filenames, '*.dcm'):
            matches.append(os.path.join(root, filename))
            if root not in dirs:
                dirs.append(root)

    return (matches, dirs)


def getAllSeries(dirs):
    """Get all the Dicom series in a set of directories."""
    isr = sitk.ImageSeriesReader()
    seriessets = []
    for d in dirs:
        series = isr.GetGDCMSeriesIDs(d)
        for s in series:
            files = isr.GetGDCMSeriesFileNames(d, s)
            print(s, d, len(files))
            seriessets.append([s, d, files])
    return seriessets


def getModality(img):
    """Get an image's modality, as stored in the Dicom meta data."""
    modality = ""
    if (sitk.Version.MinorVersion() > 8) or (sitk.Version.MajorVersion() > 0):
        try:
            modality = img.GetMetaData("0008|0060")
        except:
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
    """ Unzip a zipfile of dicom images into a temp directory, then
        load the series that has the most slices.
    """

    print("Reading Dicom zip file:", name)
    myzip = zipfile.ZipFile(name, 'r')

    try:
        myzip.extractall(tempDir)
    except:
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

    files, dirs = scanDirForDicom(sys.argv[1])
    print("")
    print("files")
    print(files)
    print("")
    print("dirs")
    print(dirs)

    print("series")
    seriessets = getAllSeries(dirs)
    for ss in seriessets:
        print(ss[0], " ", ss[1])
        print(len(ss[2]))
        print("")
