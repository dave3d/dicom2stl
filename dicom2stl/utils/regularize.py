#! /usr/bin/env python

import getopt
import sys
import SimpleITK as sitk

# Regularize a volume.  I.e. resample it so that the voxels are cubic and the
# orientation matrix is identity.
#


def regularize(img, maxdim=-1, verbose=False):
    dims = img.GetSize()

    if verbose:
        print("Input dims:", dims)
        print("Input origin:", img.GetOrigin())
        print("Input direction:", img.GetDirection())

    # corners of the volume in volume space
    vcorners = [
        [0, 0, 0],
        [dims[0], 0, 0],
        [0, dims[1], 0],
        [dims[0], dims[1], 0],
        [0, 0, dims[2]],
        [dims[0], 0, dims[2]],
        [0, dims[1], dims[2]],
        [dims[0], dims[1], dims[2]],
    ]

    # compute corners of the volume on world space
    wcorners = []
    mins = [1e32, 1e32, 1e32]
    maxes = [-1e32, -1e32, -1e32]
    for c in vcorners:
        wcorners.append(img.TransformContinuousIndexToPhysicalPoint(c))

    # compute the bounding box of the volume
    for c in wcorners:
        for i in range(0, 3):
            if c[i] < mins[i]:
                mins[i] = c[i]
            if c[i] > maxes[i]:
                maxes[i] = c[i]

    if verbose:
        print("Bound min:", mins)
        print("Bound max:", maxes)

    # if no maxdim is specified, get the max dim of the input volume.
    # this is used as the max dimension of the new volume.
    if maxdim < 0:
        maxdim = max(dims[0], dims[1])
        maxdim = max(maxdim, dims[2])

    # compute the voxel spacing of the new volume. voxels
    # will be cubic, i.e. the spacing is the same in all directions.
    maxrange = 0.0
    for i in range(0, 3):
        r = maxes[i] - mins[i]
        if r > maxrange:
            maxrange = r
    newspacing = maxrange / maxdim
    if verbose:
        print("new spacing:", newspacing)

    # compute the dimensions of the new volume
    newdims = []
    for i in range(0, 3):
        newdims.append(int((maxes[i] - mins[i]) / newspacing + 0.5))
    if verbose:
        print("new dimensions:", newdims)

    # resample the input volume into our new volume
    newimg = sitk.Resample(
        img,
        newdims,
        sitk.Transform(),
        sitk.sitkLinear,
        mins,
        [newspacing, newspacing, newspacing],
        [1, 0, 0, 0, 1, 0, 0, 0, 1],
        img.GetPixelID(),
    )

    return newimg


def usage():
    print("")
    print("regularize.py [options] input_volume output_volume")
    print("")
    print(" -v       Verbose")
    print(" -d int   Max dim")
    print("")


if __name__ == "__main__":

    if len(sys.argv) == 1:
        # no input file.  just do a test
        img = sitk.GaussianSource(
            sitk.sitkUInt8,
            size=[256, 256, 74],
            sigma=[20, 20, 5],
            mean=[128, 128, 37],
            scale=255,
        )
        img.SetSpacing([0.4, 0.4, 2.0])
        img.SetOrigin([25.0, 50.0, 75.0])
        a = 0.70710678
        c = a
        s = a
        img.SetDirection([c, s, 0, c, -s, 0, 0, 0, 1])
        sitk.WriteImage(img, "testimg.nrrd")

        outimg = regularize(img, 200)
        sitk.WriteImage(outimg, "testoutimg.nrrd")
        print(outimg)

    else:
        try:
            opts, args = getopt.getopt(
                sys.argv[1:], "vhd:", ["verbose", "help", "dim="]
            )
        except getopt.GetoptError as err:
            print(str(err))
            usage()
            sys.exit(1)

        maxdim = 128
        verbose = False

        for o, a in opts:
            if o in ("-h", "--help"):
                usage()
                sys.exit()
            elif o in ("-v", "--verbose"):
                verbose = True
            elif o in ("-d", "--dim"):
                maxdim = int(a)
            else:
                assert False, "unhandled option"

        if len(args) < 2:
            usage()
            sys.exit(1)

        inname = args[0]
        outname = args[1]

        img = sitk.ReadImage(inname)
        out_img = regularize(img, maxdim, verbose)
        sitk.WriteImage(out_img, outname)
