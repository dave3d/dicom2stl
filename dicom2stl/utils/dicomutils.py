#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pydicom>=3.0.1",
#   "SimpleITK>=2.5.3",
# ]
# ///

"""
Function to load the largest Dicom series in a directory.

It scans the directory recursively search for files with the ".dcm"
suffix. DICOM files don't always have that suffix, so files without
it are also accepted if they start with the DICOM file header.

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
from typing import List, Optional, Tuple
import SimpleITK as sitk

from pydicom.misc import is_dicom


def testDicomFile(file_path: str) -> bool:
    """Test if given file is in DICOM format.

    Only the start of the file is read, to look for the DICOM file header
    (a 128 byte preamble followed by "DICM").

    Args:
        file_path: Path to file to test

    Returns:
        True if file has the DICOM file header, False otherwise or if the
        file cannot be read
    """
    try:
        # Opening a named pipe would block, so only look at regular files.
        return os.path.isfile(file_path) and is_dicom(file_path)
    except OSError:
        return False


def scanDirForDicom(dicomdir: str) -> Tuple[List[str], List[str]]:
    """Scan directory recursively for DICOM files.

    A file is taken to be DICOM if its name ends in ".dcm" or, failing
    that, if it starts with the DICOM file header. The DICOMDIR index of
    a DICOM media set has that header too, but it is not an image, so it
    is left out.

    Args:
        dicomdir: Directory path to scan for DICOM files

    Returns:
        Tuple of (list of DICOM file paths, list of directories containing DICOM files)
    """
    matches = []
    found_dirs = []
    try:
        for root, _, filenames in os.walk(dicomdir):
            for filename in filenames:
                if filename.upper() == "DICOMDIR":
                    continue
                path = os.path.join(root, filename)
                if fnmatch.fnmatch(filename, "*.dcm") or testDicomFile(path):
                    matches.append(path)
                    if root not in found_dirs:
                        found_dirs.append(root)
    except OSError as e:
        print("Error in scanDirForDicom:", e)
        print("dicomdir =", dicomdir)

    return (matches, found_dirs)


def getAllSeries(target_dirs: List[str]) -> List[List]:
    """Get all the DICOM series in a set of directories.

    Args:
        target_dirs: List of directory paths to scan for DICOM series

    Returns:
        List of series information, where each element is [series_id, directory, file_list]
    """
    isr = sitk.ImageSeriesReader()
    found_series = []
    for d in target_dirs:
        series = isr.GetGDCMSeriesIDs(d)
        for s in series:
            found_files = isr.GetGDCMSeriesFileNames(d, s)
            print(s, d, len(found_files))
            found_series.append([s, d, found_files])
    return found_series


def getModality(img: sitk.Image) -> str:
    """Get an image's modality from DICOM metadata.

    Args:
        img: SimpleITK image with DICOM metadata

    Returns:
        Modality string (e.g., 'CT', 'MR'), or empty string if not found
    """
    modality = ""
    if (sitk.Version.MinorVersion() > 8) or (sitk.Version.MajorVersion() > 0):
        try:
            modality = img.GetMetaData("0008|0060")
        except RuntimeError:
            modality = ""
    return modality


def loadLargestSeries(dicomdir: str) -> Optional[Tuple[sitk.Image, str]]:
    """Load the largest DICOM series found in a directory.

    Scans the directory recursively for DICOM files and loads the series
    with the most slices.

    Args:
        dicomdir: Directory path to scan

    Returns:
        Tuple of (SimpleITK image, modality string), or None if no series found
    """

    files, dirs = scanDirForDicom(dicomdir)

    if (len(files) == 0) or (len(dirs) == 0):
        print("Error in loadLargestSeries. No files found.")
        print("dicomdir =", dicomdir)
        return None
    seriessets = getAllSeries(dirs)
    maxsize = 0
    maxindex = -1

    for count, ss in enumerate(seriessets):
        size = len(ss[2])
        if size > maxsize:
            maxsize = size
            maxindex = count
    if maxindex < 0:
        print("Error: no series found")
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


def loadZipDicom(name: str, tempDir: str) -> Optional[Tuple[sitk.Image, str]]:
    """Extract and load DICOM series from a ZIP file.

    Unzips DICOM images to a temporary directory and loads the series
    with the most slices.

    Args:
        name: Path to ZIP file containing DICOM images
        tempDir: Temporary directory for extraction

    Returns:
        Tuple of (SimpleITK image, modality string), or None if loading fails
    """
    print("Reading Dicom zip file:", name)
    print("tempDir =", tempDir)
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
    if len(sys.argv) < 2:
        print("Usage: dicomutils.py <dicom_directory>")
        sys.exit(1)

    print("\ndicomutils.py")
    print("Scanning:", sys.argv[1])

    dcm_files, dcm_dirs = scanDirForDicom(sys.argv[1])

    print("\nFiles found:")
    for f in dcm_files:
        print(" ", f)

    print("\nDirectories:")
    for d in dcm_dirs:
        print(" ", d)

    print("\nSeries:")
    series_found = getAllSeries(dcm_dirs)
    for sf in series_found:
        print(f"  {sf[0]} in {sf[1]}")
        print(f"    {len(sf[2])} files\n")
