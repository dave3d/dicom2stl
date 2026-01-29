#! /usr/bin/env python

"""Command line argument parsing for dicom2stl.

This module defines all command-line arguments and options for the dicom2stl tool,
including volume processing options, mesh processing options, and filtering controls.
"""

import argparse
from typing import Any, List, Optional, Sequence
from importlib.metadata import version, PackageNotFoundError

__version__ = "unknown"

try:
    __version__ = version("dicom2stl")
except PackageNotFoundError:
    # package is not installed
    pass


class disableFilter(argparse.Action):
    """Custom argparse action to disable a filter by prepending 'no' to its name."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        args: argparse.Namespace,
        values: Any,
        option_string: Optional[str] = None
    ) -> None:
        noval = "no" + values
        if args.filters is None:
            args.filters = [noval]
        else:
            args.filters.append(noval)


class enableAnisotropic(argparse.Action):
    """Custom argparse action to enable anisotropic filtering."""

    def __init__(self, nargs: int = 0, **kw: Any) -> None:
        super().__init__(nargs=nargs, **kw)

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        args: argparse.Namespace,
        values: Any,
        option_string: Optional[str] = None
    ) -> None:
        if args.filters is None:
            args.filters = ["anisotropic"]


class enableLargest(argparse.Action):
    """Custom argparse action to enable filtering for largest connected component."""

    def __init__(self, nargs: int = 0, **kw: Any) -> None:
        super().__init__(nargs=nargs, **kw)

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        args: argparse.Namespace,
        values: Any,
        option_string: Optional[str] = None
    ) -> None:
        if args.filters is None:
            args.filters = []
        args.filters.append("largest")


def createParser() -> argparse.ArgumentParser:
    """Create and configure the command line argument parser.
    
    Returns:
        Configured ArgumentParser with all dicom2stl options
    """
    parser = argparse.ArgumentParser(
        prog="dicom2stl",
        description="Convert DICOM files to STL surface mesh",
        epilog="For more information, visit: https://github.com/dave3d/dicom2stl"
    )

    parser.add_argument("filenames", nargs="*")

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        dest="verbose",
        help="Enable verbose output messages",
    )

    parser.add_argument(
        "--debug",
        "-D",
        action="store_true",
        default=False,
        dest="debug",
        help="Enable detailed debugging messages",
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
        choices=["skin", "bone", "soft", "fat"],
        help="Tissue type for CT extraction (skin, bone, soft tissue, or fat)",
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
        help='Double threshold with 4 semicolon-separated floats (e.g., "100;200;300;400")',
    )

    # Options that apply to the mesh processing portion of the pipeline
    mesh_group = parser.add_argument_group("Mesh options")
    mesh_group.add_argument(
        "--largest",
        "-l",
        action=enableLargest,
        help="Keep only the largest connected component of the mesh",
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
        help="Rotation angle in degrees (default=0.0)",
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
        help="Mesh reduction/decimation factor, 0.0-1.0 (default=0.9, reduces by 90%%)",
    )

    mesh_group.add_argument(
        "--clean-small",
        "-x",
        action="store",
        dest="small",
        type=float,
        default=0.05,
        help="Remove disconnected components smaller than this ratio of largest (default=0.05)",
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


def parseargs() -> argparse.Namespace:
    """Parse command line arguments and return the parsed namespace.
    
    Returns:
        Namespace object containing all parsed arguments
    """
    parser = createParser()
    args = parser.parse_args()
    return args
