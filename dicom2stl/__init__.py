import dicom2stl
import dicom2stl.utils.parseargs
def main():
    """Entry point for the application script"""
    args = dicom2stl.utils.parseargs.parseargs()
    dicom2stl.Dicom2STL(args)
