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

For DICOM series with irregular slice spacing or gaps, use -D instead of
passing a directory as a positional argument.  -D reads every .dcm file
individually and places each slice at its true Image Position Patient
coordinate.  Gaps between slices are filled automatically by linear
interpolation along the slice-normal axis.

Usage
-----
    resample_to_volume.py [options] image1 image2 ... output_volume
    resample_to_volume.py [options] -D dicom_dir output_volume

Options
-------
    -s, --spacing FLOAT   Isotropic output voxel spacing in mm (default: auto)
    -x FLOAT              Output spacing along X axis
    -y FLOAT              Output spacing along Y axis
    -z FLOAT              Output spacing along Z axis
    -t, --thickness FLOAT Slice thickness in mm for promoted 2-D slices; if omitted,
                          uses DICOM SliceThickness (0018|0050) for -D and otherwise
                          keeps SimpleITK defaults.
    -D, --dicom-dir DIR   Directory of DICOM slices to load individually (repeatable)
    -i, --interp STR      Interpolator: linear (default), nearest, bspline, gaussian
    -p, --pad FLOAT       Padding value for voxels outside every input image (default: 0)
    -v, --verbose         Print progress information
    -h, --help            Show this help message
"""

import argparse
import bisect
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

PIXEL_TYPES = {
    "uint8":   sitk.sitkUInt8,
    "int8":    sitk.sitkInt8,
    "uint16":  sitk.sitkUInt16,
    "int16":   sitk.sitkInt16,
    "uint32":  sitk.sitkUInt32,
    "int32":   sitk.sitkInt32,
    "float32": sitk.sitkFloat32,
    "float64": sitk.sitkFloat64,
}


def load_image(path: str, thickness: float | None = None) -> sitk.Image:
    """Load an image file; promote 2-D images to 3-D single-slice volumes.

    Parameters
    ----------
    path:
        Path to the image file.
    thickness:
        Slice thickness (mm) to assign to the through-plane axis when a 2-D
        image is promoted to 3-D.  Has no effect on images that are already
        3-D.  Defaults to ``None`` (keep whatever spacing SimpleITK assigns,
        typically 1.0 mm).
    """
    img = sitk.ReadImage(path)
    if img.GetDimension() == 2:
        img = sitk.JoinSeries(img)
        if thickness is not None:
            thickness = float(thickness)
            if thickness <= 0:
                raise ValueError(f"{path}: thickness must be > 0 (got {thickness}).")
            sp = list(img.GetSpacing())
            sp[2] = thickness
            img.SetSpacing(sp)
    if img.GetDimension() != 3:
        raise ValueError(f"{path}: only 2-D and 3-D images are supported.")
    return img


def _dicom_3d_geometry(
    img2d: sitk.Image,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Return ``(origin3d, direction3d)`` for a 2-D DICOM image.

    Reads the Image Position Patient (0020|0032) and Image Orientation
    Patient (0020|0037) DICOM tags so that each slice is placed at its true
    location in 3-D space regardless of whether the series has regular spacing.

    Falls back to a z = 0 origin and the identity direction when the tags are
    absent (e.g. non-DICOM images passed by mistake).
    """
    try:
        ipp = [float(v) for v in img2d.GetMetaData("0020|0032").split("\\")]
        if len(ipp) != 3:
            raise ValueError(f"IPP has {len(ipp)} value(s)")
        origin3d: tuple[float, ...] = (ipp[0], ipp[1], ipp[2])
    except (RuntimeError, ValueError, IndexError):
        o = img2d.GetOrigin()
        origin3d = (float(o[0]), float(o[1]), float(o[2]) if len(o) > 2 else 0.0)

    try:
        iop = [float(v) for v in img2d.GetMetaData("0020|0037").split("\\")]
        if len(iop) != 6:
            raise ValueError(f"IOP has {len(iop)} value(s)")
        row_cos = np.array(iop[:3], dtype=float)
        col_cos = np.array(iop[3:], dtype=float)

        row_cos /= np.linalg.norm(row_cos) or 1.0
        col_cos /= np.linalg.norm(col_cos) or 1.0
        normal = np.cross(row_cos, col_cos)
        normal /= np.linalg.norm(normal) or 1.0

        # SimpleITK direction matrices are stored row-major with *columns*
        # equal to the physical directions of each index axis.
        d_mat = np.column_stack([row_cos, col_cos, normal])
        direction3d: tuple[float, ...] = tuple(float(v) for v in d_mat.flatten())
    except (RuntimeError, ValueError, IndexError):
        direction3d = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)

    return origin3d, direction3d


def load_dicom_slices(
    directory: str,
    thickness: float | None = None,
) -> list[sitk.Image]:
    """Read each DICOM slice in *directory* as an independent single-slice 3-D volume.

    Unlike reading the whole series at once (which assumes uniform spacing),
    this function reads every file individually and positions each slice using
    the Image Position Patient tag.  The result is a list of single-slice 3-D
    images suitable for :func:`stack_images`, which handles arbitrary
    positions and gaps correctly.

    Parameters
    ----------
    directory:
        Path to a directory that contains the DICOM series files.
    thickness:
        Through-plane voxel size (mm) for each slice.  When ``None`` the
        SliceThickness DICOM tag (0018|0050) is consulted; if that tag is
        also absent, 1.0 mm is assumed.
    """
    series_ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(directory)
    if not series_ids:
        raise ValueError(f"No DICOM series found in: {directory}")
    if len(series_ids) > 1:
        logging.warning(
            "%s contains %d DICOM series; loading the first one (%s).",
            directory, len(series_ids), series_ids[0],
        )

    dcm_files = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(
        directory, series_ids[0]
    )

    file_reader = sitk.ImageFileReader()
    file_reader.SetImageIO("GDCMImageIO")
    file_reader.LoadPrivateTagsOn()

    slices: list[sitk.Image] = []
    for path in dcm_files:
        file_reader.SetFileName(path)
        img_read = file_reader.Execute()

        # GDCM may return a 3-D single-slice image rather than a 2-D one;
        # calling JoinSeries on a 3-D image would produce a 4-D result.
        if img_read.GetDimension() == 2:
            img3d = sitk.JoinSeries(img_read)
        elif img_read.GetDimension() == 3:
            img3d = img_read
        else:
            raise ValueError(
                f"{path}: unexpected image dimension {img_read.GetDimension()}."
            )

        origin3d, direction3d = _dicom_3d_geometry(img_read)

        if thickness is not None:
            z_sp = float(thickness)
        else:
            try:
                z_sp = float(img_read.GetMetaData("0018|0050"))
            except RuntimeError:
                z_sp = 1.0

        if z_sp <= 0:
            raise ValueError(f"{path}: invalid slice thickness {z_sp}; must be > 0.")

        sp = list(img3d.GetSpacing())
        sp[2] = z_sp
        img3d.SetSpacing(tuple(sp))
        img3d.SetOrigin(origin3d)
        img3d.SetDirection(direction3d)

        slices.append(img3d)

    return slices


def _covered_z_planes(
    slices: list[sitk.Image],
    size: tuple[int, ...],
    spacing: tuple[float, ...],
    origin: tuple[float, ...],
    direction: tuple[float, ...],
) -> list[int]:
    """Return a sorted list of output Z-plane indices covered by *slices*.

    Each single-slice 3-D image maps to the output Z plane whose physical
    position is closest to the slice's origin along the output Z axis.
    """
    rot = np.array(direction).reshape(3, 3)
    sz = spacing[2]
    nz = size[2]
    o_ref = np.array(origin)
    covered: set[int] = set()
    for img in slices:
        local_z = float((rot.T @ (np.array(img.GetOrigin()) - o_ref))[2])
        k = int(round(local_z / sz))
        if 0 <= k < nz:
            covered.add(k)
    return sorted(covered)


def fill_slice_gaps(
    volume: sitk.Image,
    covered: list[int],
    _default_value: float,
) -> sitk.Image:
    """Fill uncovered Z planes in *volume* by linear interpolation.

    For each output Z plane that has no corresponding input slice, the voxel
    values are replaced by a weighted blend of the nearest covered planes
    above and below.  Planes beyond the extent of all input slices are filled
    with the nearest covered plane (no extrapolation).

    Parameters
    ----------
    volume:
        The assembled 3-D volume (float32).
    covered:
        Sorted list of Z-plane indices that have real data from input slices.
        Obtain this from :func:`_covered_z_planes`.
    _default_value:
        Unused; kept for API symmetry.
    """
    if not covered:
        return volume

    arr = sitk.GetArrayFromImage(volume).astype(np.float32)  # shape: (Z, Y, X)
    nz = arr.shape[0]
    covered_set = set(covered)

    for k in range(nz):
        if k in covered_set:
            continue
        pos = bisect.bisect_left(covered, k)
        k_lo = covered[pos - 1] if pos > 0 else None
        k_hi = covered[pos] if pos < len(covered) else None

        if k_lo is not None and k_hi is not None:
            alpha = float(k - k_lo) / float(k_hi - k_lo)
            arr[k] = (1.0 - alpha) * arr[k_lo] + alpha * arr[k_hi]
        elif k_lo is not None:
            arr[k] = arr[k_lo]
        elif k_hi is not None:
            arr[k] = arr[k_hi]

    result = sitk.GetImageFromArray(arr)
    result.CopyInformation(volume)
    return result


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
    parser.add_argument("-t", "--thickness", type=float, default=None, metavar="MM",
                        help=("Slice thickness in mm for promoted 2-D slices. "
                              "If omitted, uses DICOM SliceThickness (0018|0050) "
                              "for -D and otherwise keeps SimpleITK defaults."))
    parser.add_argument("-D", "--dicom-dir", action="append", default=None,
                        metavar="DIR", dest="dicom_dirs",
                        help="Directory of DICOM slices to load individually "
                             "(may be repeated for multiple series).")
    parser.add_argument("-p", "--pad", type=float, default=0.0, metavar="VALUE",
                        help="Fill value for voxels outside all inputs (default: 0).")
    parser.add_argument("-T", "--type", default=None, dest="pixel_type",
                        choices=list(PIXEL_TYPES),
                        help="Output pixel type (default: same as first input).")
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


def main(argv: list[str] | None = None) -> int:  # pylint: disable=too-many-locals
    """Entry point: parse arguments, resample inputs, write output."""
    args = parse_args(sys.argv[1:] if argv is None else argv)

    has_dicom_dirs = bool(args.dicom_dirs)
    min_positional = 1 if has_dicom_dirs else 2
    if len(args.inputs) < min_positional:
        if has_dicom_dirs:
            print("Error: provide an output path.")
        else:
            print("Error: provide at least one input image and one output path.")
        return 1

    *input_paths, output_path = args.inputs

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(message)s",
    )

    # Load images.
    dicom_slices: list[sitk.Image] = []

    # Per-slice DICOM loading (handles irregular spacing / gaps).
    for dicom_dir in (args.dicom_dirs or []):
        logging.info("Loading DICOM series from %s (per-slice)", dicom_dir)
        slices = load_dicom_slices(dicom_dir, thickness=args.thickness)
        logging.info("  found %d slice(s)", len(slices))
        dicom_slices.extend(slices)

    images: list[sitk.Image] = list(dicom_slices)
    for p in input_paths:
        logging.info("Loading %s", p)
        images.append(load_image(p, thickness=args.thickness))

    # Resolve spacing.
    requested_spacing = build_spacing(args)

    # If per-axis spacing has None entries, fill from finest input spacing.
    if requested_spacing is not None and any(v is None for v in requested_spacing):
        finest = [min(img.GetSpacing()[i] for img in images) for i in range(3)]
        requested_spacing = [
            requested_spacing[i] if requested_spacing[i] is not None else finest[i]
            for i in range(3)
        ]

    # Remember the pixel type of the first *positional* input if provided; otherwise
    # fall back to the first DICOM slice.
    first_input_img = images[len(dicom_slices)] if input_paths else images[0]
    input_pixel_type = first_input_img.GetPixelID()

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

    # Fill gaps between irregularly-spaced DICOM slices by linear interpolation.
    # Only do this in DICOM-only mode; otherwise it can overwrite data coming
    # from non-DICOM inputs that happen to lie on uncovered Z planes.
    if dicom_slices and not input_paths:
        logging.info("Filling gaps between DICOM slices …")
        covered = _covered_z_planes(dicom_slices, size, spacing, origin, direction)
        logging.info(
            "  %d / %d Z planes covered by input slices", len(covered), size[2]
        )
        volume = fill_slice_gaps(volume, covered, args.pad)
    elif dicom_slices:
        logging.warning(
            "Skipping DICOM gap filling because non-DICOM inputs are also provided."
        )
    # Cast to the requested output type, or fall back to the first input's type.
    out_pixel_type = PIXEL_TYPES[args.pixel_type] if args.pixel_type else input_pixel_type
    if volume.GetPixelID() != out_pixel_type:
        volume = sitk.Cast(volume, out_pixel_type)

    # Write output.
    logging.info("Writing %s", output_path)
    sitk.WriteImage(volume, output_path, useCompression=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
