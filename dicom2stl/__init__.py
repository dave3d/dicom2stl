import dicom2stl.utils.parseargs
import dicom2stl.Dicom2STL
def main():
    """Entry point for the application script"""
    print("Call your main application code here")
    args = parseargs.parseargs()
    dicom2stl_func.Dicom2STL(args)
