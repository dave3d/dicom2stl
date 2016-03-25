#! /usr/bin/env python

#
#  Function to load the largest Dicom series in a directory.
#
#  It scans the directory recursively search for files with the ".dcm"
#  suffix.  Note that DICOM fails don't always have that suffix.  In
#  that case this function will fail.
#
#  Written by David T. Chen from the National Library of Medicine, dchen@mail.nih.gov.
#  It is covered by the Apache License, Version 2.0:
#      http://www.apache.org/licenses/LICENSE-2.0
#

import sys, os, fnmatch
import zipfile
import SimpleITK as sitk


def scanDirForDicom(dicomdir):
    matches = []
    dirs = []
    for root, dirnames, filenames in os.walk(dicomdir):
        for filename in fnmatch.filter(filenames, '*.dcm'):
            matches.append(os.path.join(root, filename));
            if root not in dirs:
                dirs.append(root)

    return (matches, dirs)

def getAllSeries(dirs):
    isr = sitk.ImageSeriesReader()
    seriessets = []
    for d in dirs:
        series = isr.GetGDCMSeriesIDs(d)
        for s in series:
            files = isr.GetGDCMSeriesFileNames(d, s)
            print s, d, len(files)
            seriessets.append([s, d, files])
    return seriessets

def getModality(img):
    modality = ""
    if (sitk.Version.MinorVersion()>8) or (sitk.Version.MajorVersion()>0):
        try:
            modality = img.GetMetaData("0008|0060")
        except:
            modality = ""
    return modality


#   Load the largest Dicom series it finds in a recursive scan of
#   a directory.  Largest means has the most slices.  It also returns
#   the modality.
#
def loadLargestSeries(dicomdir):
    files, dirs = scanDirForDicom(dicomdir)
    seriessets = getAllSeries(dirs)
    maxsize = 0
    maxindex = -1

    count = 0
    for ss in seriessets:
        size = len(ss[2])
        if size>maxsize:
            maxsize = size
            maxindex = count
        count = count + 1
    if maxindex<0:
        print "Error:  no series found"
        return None
    isr = sitk.ImageSeriesReader()
    ss = seriessets[maxindex]
    files = ss[2]
    isr.SetFileNames(files)
    print "\nLoading series", ss[0], "in directory", ss[1]
    img = isr.Execute()

    firstslice = sitk.ReadImage(files[0])
    modality = getModality(firstslice)

    return img, modality


#
#   Main (test code)
#

if __name__ == "__main__":
    print ""
    print "dicomutils.py"
    print sys.argv[1]

#    img = loadLargestSeries(sys.argv[1])
#    print img
#    sys.exit(0)

    files, dirs = scanDirForDicom(sys.argv[1])
    print ""
    print "files"
    print files
    print ""
    print "dirs"
    print dirs

    print "series"
    seriessets = getAllSeries(dirs)
    for ss in seriessets:
       print ss[0], " ", ss[1]
       print len(ss[2])
       print ""


