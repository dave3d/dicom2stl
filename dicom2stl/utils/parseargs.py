#! /usr/bin/env python

""" Command line argument parsing for dicom2stl """
import argparse

from importlib.metadata import version, PackageNotFoundError

__version__ = "unknown"

try:
    __version__ = version("dicom2stl")
except PackageNotFoundError:
    # package is not installed
    pass


class disableFilter(argparse.Action):
    """Disable a filter"""

    def __call__(self, parser, args, values, option_string=None):
        # print("action, baby!", self.dest, values)
        # print(args, type(args))
        noval = "no" + values
        if isinstance(args.filters, type(None)):
            args.filters = [noval]
        else:
            args.filters.append(noval)


class enableAnisotropic(argparse.Action):
    """Enable anisotropic filtering"""

    def __init__(self, nargs=0, **kw):
        super().__init__(nargs=nargs, **kw)

    def __call__(self, parser, args, values, option_string=None):
        # x = getattr(args, 'filters')
        if isinstance(args.filters, type(None)):
            args.filters = ["anisotropic"]
        # args.filters.append('anisotropic')


class enableLargest(argparse.Action):
    """Enable filtering for large objects"""

    def __init__(self, nargs=0, **kw):
        super().__init__(nargs=nargs, **kw)

    def __call__(self, parser, args, values, option_string=None):
        x = getattr(args, "filters")
        x.append("largest")


def createParser():
    """Create the command line argument parser"""
    parser = argparse.ArgumentParser()

    parser.add_argument("filenames", nargs="*")

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        dest="verbose",
        help="Enable verbose messages",
    )

    parser.add_argument(
        "--debug",
        "-D",
        action="store_true",
        default=False,
        dest="debug",
        help="""Enable debugging messages
                        """,
    )

    parser.add_argument(
        "--output",
        "-o",
        action="store",
        dest="output",
        default="result.stl",
        help="Output file name (default=result.stl)",
    )

    parser.add_argument(
        "--meta",
        "-m",
        action="store",
        dest="meta",
        help="Output metadata file",
    )

    parser.add_argument(
        "--ct",
        action="store_true",
        default=False,
        dest="ctonly",
        help="Only allow CT Dicom as input",
    )

    parser.add_argument(
        "--clean",
        "-c",
        action="store_true",
        default=False,
        dest="clean",
        help="Clean up temp files",
    )

    parser.add_argument(
        "--temp", "-T", action="store", dest="temp", help="Temporary directory"
    )

    parser.add_argument(
        "--search",
        "-s",
        action="store",
        dest="search",
        help="Dicom series search string",
    )

    parser.add_argument("--version", action="version", version=f"{__version__}")

    # Options that apply to the volumetric portion of the pipeline
    vol_group = parser.add_argument_group("Volume options")

    vol_group.add_argument(
        "--type",
        "-t",
        action="store",
        dest="tissue",
        choices=["skin", "bone", "soft_tissue", "fat"],
        help="CT tissue type",
    )

    vol_group.add_argument(
        "--anisotropic",
        "-a",
        action=enableAnisotropic,
        help="Apply anisotropic smoothing to the volume",
    )

    vol_group.add_argument(
        "--isovalue",
        "-i",
        action="store",
        dest="isovalue",
        type=float,
        default=0.0,
        help="Iso-surface value",
    )

    vol_group.add_argument(
        "--double",
        "-d",
        action="store",
        dest="double_threshold",
        help="""Double threshold with 4 semicolon separated floats
                                """,
    )

    # Options that apply to the mesh processing portion of the pipeline
    mesh_group = parser.add_argument_group("Mesh options")
    mesh_group.add_argument(
        "--largest",
        "-l",
        action=enableLargest,
        help="Only keep the largest connected sub-mesh",
    )

    mesh_group.add_argument(
        "--rotaxis",
        action="store",
        dest="rotaxis",
        default="Y",
        choices=["X", "Y", "Z"],
        help="Rotation axis (default=Y)",
    )

    mesh_group.add_argument(
        "--rotangle",
        action="store",
        dest="rotangle",
        type=float,
        default=0.0,
        help="Rotation angle in degrees (default=180)",
    )

    mesh_group.add_argument(
        "--smooth",
        action="store",
        dest="smooth",
        type=int,
        default=25,
        help="Mesh smoothing iterations (default=25)",
    )

    mesh_group.add_argument(
        "--reduce",
        action="store",
        dest="reduce",
        type=float,
        default=0.9,
        help="Mesh reduction factor (default=.9)",
    )

    mesh_group.add_argument(
        "--clean-small",
        "-x",
        action="store",
        dest="small",
        type=float,
        default=0.05,
        help="Clean small parts factor (default=.05)",
    )

    # Filtering options
    filter_group = parser.add_argument_group("Filtering options")
    filter_group.add_argument(
        "--enable",
        action="append",
        dest="filters",
        choices=["anisotropic", "shrink", "median", "largest", "rotation"],
        help="Enable filtering options",
    )
    filter_group.add_argument(
        "--disable",
        action=disableFilter,
        dest="filters",
        choices=["anisotropic", "shrink", "median", "largest", "rotation"],
        help="Disable filtering options",
    )

    return parser


def parseargs():
    """Parse the command line arguments"""
    parser = createParser()
    args = parser.parse_args()
    return args
