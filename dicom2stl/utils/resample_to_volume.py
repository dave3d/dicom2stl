#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "numpy",
#   "SimpleITK",
# ]
# ///

"""
Resample an arbitrary set of images into a uniform 3D volume.

Each input image is resampled into a common reference space defined by
a uniform isotropic (or user-specified) voxel spacing.  The reference
grid is computed from the bounding box that encompasses all input images,
so images with different sizes, spacings, origins, and orientations are
all handled correctly.

Inputs can be any format that SimpleITK can read (NRRD, NIfTI, MHD,
DICOM, PNG, TIFF, …).  2-D inputs are treated as single-slice volumes.

Usage
-----
    resample_to_volume.py [options] image1 image2 ... output_volume

Options
-------
    -s, --spacing FLOAT   Isotropic output voxel spacing in mm (default: auto)
    -x FLOAT              Output spacing along X axis
    -y FLOAT              Output spacing along Y axis
    -z FLOAT              Output spacing along Z axis
    -i, --interp STR      Interpolator: linear (default), nearest, bspline, gaussian
    -p, --pad FLOAT       Padding value for voxels outside every input image (default: 0)
    -v, --verbose         Print progress information
    -h, --help            Show this help message
"""

import argparse
import sys
import logging

import numpy as np
import SimpleITK as sitk


INTERPOLATORS = {
    "linear":   sitk.sitkLinear,
    "nearest":  sitk.sitkNearestNeighbor,
    "bspline":  sitk.sitkBSpline,
    "gaussian": sitk.sitkGaussian,
}


def load_image(path: str) -> sitk.Image:
    """Load an image file; promote 2-D images to 3-D single-slice volumes."""
    img = sitk.ReadImage(path)
    if img.GetDimension() == 2:
        img = sitk.JoinSeries(img)
    if img.GetDimension() != 3:
        raise ValueError(f"{path}: only 2-D and 3-D images are supported.")
    return img


def _collect_corners(images: list[sitk.Image], rotation: np.ndarray) -> np.ndarray:
    """Return all bounding-box corner points of each image rotated into the reference frame."""
    corners = []
    for img in images:
        sz = img.GetSize()
        for ci in (
            [i, j, k]
            for i in (0, sz[0] - 1)
            for j in (0, sz[1] - 1)
            for k in (0, sz[2] - 1)
        ):
            phys = img.TransformIndexToPhysicalPoint(ci)
            corners.append(rotation.T @ np.array(phys))
    return np.array(corners)


def compute_reference_grid(
    images: list[sitk.Image],
    out_spacing: list[float] | None,
) -> tuple[tuple[int, ...], tuple[float, ...], tuple[float, ...], tuple[float, ...]]:
    """
    Compute origin, spacing, direction, and size for a grid that covers the
    physical bounding box of all input images.

    Returns
    -------
    (size, spacing, origin, direction)
    """
    # Use the direction of the first image as the reference orientation.
    ref_direction = images[0].GetDirection()

    # Build a 3-D rotation matrix from the direction cosines and collect
    # all physical bounding-box corners in that reference frame.
    rotation = np.array(ref_direction).reshape(3, 3)
    corners = _collect_corners(images, rotation)
    min_pt = corners.min(axis=0)
    max_pt = corners.max(axis=0)

    # Determine output spacing.
    if out_spacing is None:
        # Use the finest spacing across all images (per axis).
        spacings = np.array([img.GetSpacing() for img in images])
        out_spacing = spacings.min(axis=0).tolist()
    if any(s is None for s in out_spacing) or any(float(s) <= 0 for s in out_spacing):
        raise ValueError(
            f"Invalid output spacing {out_spacing}; spacing must be > 0 for all axes."
        )
    spacing = tuple(float(s) for s in out_spacing)

    # Size in voxels to cover the bounding box.
    extent = max_pt - min_pt
    size = tuple(
        max(1, int(np.ceil(extent[i] / spacing[i])) + 1) for i in range(3)
    )

    # Origin: corner of the bounding box rotated back to physical space.
    origin = tuple(float(v) for v in (rotation @ min_pt).tolist())

    return size, spacing, origin, ref_direction


def resample_to_reference(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    image: sitk.Image,
    size: tuple[int, ...],
    spacing: tuple[float, ...],
    origin: tuple[float, ...],
    direction: tuple[float, ...],
    interpolator: int,
    default_value: float,
) -> sitk.Image:
    """Resample *image* onto the given reference grid."""
    return sitk.Resample(
        image,
        size,
        sitk.Transform(),
        interpolator,
        origin,
        spacing,
        direction,
        default_value,
        sitk.sitkFloat32,
    )


def stack_images(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    images: list[sitk.Image],
    size: tuple[int, ...],
    spacing: tuple[float, ...],
    origin: tuple[float, ...],
    direction: tuple[float, ...],
    interpolator: int,
    default_value: float,
) -> sitk.Image:
    """
    Resample all images onto the reference grid and combine them by taking
    the maximum value at each voxel (foreground wins over padding).

    For a single image this is a straightforward resample.
    """
    resampled = [
        resample_to_reference(
            img, size, spacing, origin, direction, interpolator, default_value
        )
        for img in images
    ]

    if len(resampled) == 1:
        return resampled[0]

    # Combine with max in float32 to avoid precision loss, and keep float output.
    combined = sitk.Cast(resampled[0], sitk.sitkFloat32)
    for r in resampled[1:]:
        combined = sitk.Maximum(combined, sitk.Cast(r, sitk.sitkFloat32))
    return combined


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments and return the populated Namespace."""
    parser = argparse.ArgumentParser(
        description="Resample an arbitrary set of images into a uniform 3D volume.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("inputs", nargs="+", metavar="IMAGE",
                        help="One or more input image files (last argument is the output).")
    parser.add_argument("-s", "--spacing", type=float, default=None, metavar="MM",
                        help="Isotropic output voxel spacing in mm.")
    parser.add_argument("-x", type=float, default=None, metavar="MM",
                        help="Output spacing along X axis.")
    parser.add_argument("-y", type=float, default=None, metavar="MM",
                        help="Output spacing along Y axis.")
    parser.add_argument("-z", type=float, default=None, metavar="MM",
                        help="Output spacing along Z axis.")
    parser.add_argument("-i", "--interp", default="linear",
                        choices=list(INTERPOLATORS),
                        help="Interpolation method (default: linear).")
    parser.add_argument("-p", "--pad", type=float, default=0.0, metavar="VALUE",
                        help="Fill value for voxels outside all inputs (default: 0).")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args(argv)


def build_spacing(args: argparse.Namespace) -> list[float] | None:
    """Resolve per-axis and isotropic spacing arguments."""
    if args.spacing is not None:
        return [args.spacing, args.spacing, args.spacing]
    per_axis = [args.x, args.y, args.z]
    if any(v is not None for v in per_axis):
        # Fill missing axes later when we know the finest input spacing.
        return per_axis   # may contain None entries
    return None


def main(argv: list[str] | None = None) -> int:
    """Entry point: parse arguments, resample inputs, write output."""
    args = parse_args(sys.argv[1:] if argv is None else argv)

    if len(args.inputs) < 2:
        print("Error: provide at least one input image and one output path.")
        return 1

    *input_paths, output_path = args.inputs

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(message)s",
    )

    # Load images.
    images = []
    for p in input_paths:
        logging.info("Loading %s", p)
        images.append(load_image(p))

    # Resolve spacing.
    requested_spacing = build_spacing(args)

    # If per-axis spacing has None entries, fill from finest input spacing.
    if requested_spacing is not None and any(v is None for v in requested_spacing):
        finest = [min(img.GetSpacing()[i] for img in images) for i in range(3)]
        requested_spacing = [
            requested_spacing[i] if requested_spacing[i] is not None else finest[i]
            for i in range(3)
        ]

    # Compute the reference grid.
    logging.info("Computing reference grid …")
    size, spacing, origin, direction = compute_reference_grid(images, requested_spacing)
    logging.info("  output size:    %s", size)
    logging.info("  output spacing: %s mm", spacing)
    logging.info("  output origin:  %s", origin)

    interpolator = INTERPOLATORS[args.interp]

    # Resample and combine.
    logging.info("Resampling %d image(s) …", len(images))
    volume = stack_images(
        images, size, spacing, origin, direction, interpolator, args.pad
    )

    # Write output.
    logging.info("Writing %s", output_path)
    sitk.WriteImage(volume, output_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
