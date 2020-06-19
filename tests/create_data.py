#! /usr/bin/env python

import argparse

import SimpleITK as sitk


def make_tetra(dim=128, pixel_type=sitk.sitkUInt8):
    # vertices of a tetrahedron
    tverts = [[0.732843, 0.45, 0.35],
              [0.308579, 0.694949, 0.35],
              [0.308579, 0.205051, 0.35],
              [0.45, 0.45, 0.75]]
    sigma = [dim / 6, dim / 6, dim / 6]
    size = [dim, dim, dim]

    vol = sitk.Image(size, sitk.sitkUInt8)
    for v in tverts:
        pt = [v[0] * dim, v[1] * dim, v[2] * dim]
        vol = vol + sitk.GaussianSource(pixel_type, size, sigma=sigma,
                                        mean=pt, scale=200)

    return vol


def make_cylinder(dim=64, pixel_type=sitk.sitkUInt8):
    mean = [dim / 2, dim / 2]
    sigma = [dim / 4, dim / 4]
    img = sitk.GaussianSource(pixel_type, [dim, dim], sigma=sigma, mean=mean,
                              scale=200)

    series = []
    for i in range(dim):
        series.append(img)

    vol = sitk.JoinSeries(series)
    return vol


if __name__ == "__main__":

    typemap = {"uint8": sitk.sitkUInt8, "uint16": sitk.sitkUInt16,
               "int16": sitk.sitkInt16, "int32": sitk.sitkInt32,
               "float32": sitk.sitkFloat32, "float64": sitk.sitkFloat64}

    parser = argparse.ArgumentParser()

    parser.add_argument("output", help="Output file name")

    parser.add_argument('--dim', '-d', action='store', dest='dim', type=int,
                        default=32, help='Image dimensions (default=32)')
    parser.add_argument('--pixel', '-p', action='store', dest='pixeltype',
                        default='uint8', help="Pixel type (default=\'uint8\')")

    parser.add_argument('--tetra', '-t', action='store_true', default=True,
                        dest='tetra_flag', help='Make a tetrahedral volume')

    parser.add_argument('--cylinder', '-c', action='store_false', default=True,
                        dest='tetra_flag', help='Make a cylindrical volume')

    args = parser.parse_args()

    print("args:", args)
    ptype = typemap[args.pixeltype]
    print(ptype)

    if args.tetra_flag:
        print("Making tetra")
        vol = make_tetra(args.dim, ptype)
    else:
        print("Making cylinder")
        vol = make_cylinder(args.dim, ptype)
    print("Writing", args.output)
    sitk.WriteImage(vol, args.output)
