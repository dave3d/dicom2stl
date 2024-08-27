""" dicom2stl - Convert DICOM files to STL files """
from dicom2stl import Dicom2STL
import dicom2stl.utils.parseargs


def main():
    """Entry point for the application script"""
    args = dicom2stl.utils.parseargs.parseargs()
    Dicom2STL.Dicom2STL(args)
