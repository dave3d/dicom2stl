#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "SimpleITK>=2.5.3",
# ]
# ///

"""Utility functions to create test data for DICOM to STL conversion tests."""\n\nimport argparse\n\nimport SimpleITK as sitk\n\n\ndef make_tetra(dim=128, scale=200.0, pixel_type=sitk.sitkUInt8):\n    """Create a test image with a tetrahedral shape.\n\n    Args:\n        dim: Dimension of the cubic output image\n        scale: Gaussian peak intensity scale\n        pixel_type: SimpleITK pixel type for the output image\n\n    Returns:\n        SimpleITK image with tetrahedral shape\n    """
    # vertices of a tetrahedron
    tverts = [
        [0.732843, 0.45, 0.35],
        [0.308579, 0.694949, 0.35],
        [0.308579, 0.205051, 0.35],
        [0.45, 0.45, 0.75],
    ]
    sigma = [dim / 6, dim / 6, dim / 6]
    size = [dim, dim, dim]

    vol = sitk.Image(size, pixel_type)
    for v in tverts:
        pt = [v[0] * dim, v[1] * dim, v[2] * dim]
        vol = vol + sitk.GaussianSource(
            pixel_type, size, sigma=sigma, mean=pt, scale=scale
        )

    return vol


def make_cylinder(dim=64, scale=200.0, pixel_type=sitk.sitkUInt8):\n    """Create a test image with a cylindrical shape.\n\n    Args:\n        dim: Dimension of the output image (cubic)\n        scale: Gaussian peak intensity scale\n        pixel_type: SimpleITK pixel type for the output image\n\n    Returns:\n        SimpleITK 3D image with cylindrical shape\n    """
    mean = [dim / 2, dim / 2]
    sigma = [dim / 4, dim / 4]
    img = sitk.GaussianSource(
        pixel_type, [dim, dim], sigma=sigma, mean=mean, scale=scale
    )

    series = []
    for i in range(dim):
        series.append(img)

    vol = sitk.JoinSeries(series)
    return vol


if __name__ == "__main__":

    typemap = {
        "uint8": sitk.sitkUInt8,
        "uint16": sitk.sitkUInt16,
        "int16": sitk.sitkInt16,
        "int32": sitk.sitkInt32,
        "float32": sitk.sitkFloat32,
        "float64": sitk.sitkFloat64,
    }

    parser = argparse.ArgumentParser()

    parser.add_argument("output", help="Output file name")

    parser.add_argument(
        "--dim",
        "-d",
        action="store",
        dest="dim",
        type=int,
        default=32,
        help="Image dimensions (default=32)",
    )
    parser.add_argument(
        "--pixel",
        "-p",
        action="store",
        dest="pixeltype",
        default="uint8",
        help="Pixel type (default='uint8')",
    )
    parser.add_argument(
        "--scale",
        "-s",
        action="store",
        dest="scale",
        type=float,
        default=200.0,
        help="Intensity scale (default=200.0)",
    )

    parser.add_argument(
        "--tetra",
        "-t",
        action="store_true",
        default=True,
        dest="tetra_flag",
        help="Make a tetrahedral volume",
    )

    parser.add_argument(
        "--cylinder",
        "-c",
        action="store_false",
        default=True,
        dest="tetra_flag",
        help="Make a cylindrical volume",
    )

    args = parser.parse_args()

    print("args:", args)
    ptype = typemap[args.pixeltype]
    print(ptype)

    if args.tetra_flag:
        print("Making tetra")
        vol = make_tetra(args.dim, args.scale, ptype)
    else:
        print("Making cylinder")
        vol = make_cylinder(args.dim, args.scale, ptype)
    print("Writing", args.output)
    sitk.WriteImage(vol, args.output)
