#! /usr/bin/env python

import sys
import SimpleITK as sitk
import getopt

# vertices of a tetrahedron
tverts = [ [0.732843, 0.45, 0.35],
           [0.308579, 0.694949, 0.35],
           [0.308579, 0.205051, 0.35],
           [0.45, 0.45, 0.75]]

def make_tetra(dim=128, pixel_type=sitk.sitkUInt8):

    sigma=[dim/6,dim/6,dim/6]
    size=[dim,dim,dim]

    vol = sitk.Image(size, sitk.sitkUInt8)
    for v in tverts:
        pt = [v[0]*dim, v[1]*dim, v[2]*dim]
        vol = vol + sitk.GaussianSource(pixel_type, size, sigma=sigma, mean=pt, scale=200)

    return vol

def make_cylinder(dim=64, pixel_type=sitk.sitkUInt8):
    mean=[dim/2,dim/2]
    sigma=[dim/4,dim/4]
    img = sitk.GaussianSource(pixel_type, [dim,dim], sigma=sigma, mean=mean, scale=200)

    series = []
    for i in range(dim):
        series.append(img)

    vol = sitk.JoinSeries(series)
    return vol


def usage():
    print()
    print(" create_data.py [options] output_image")
    print()
    print(" -h, --help          This message")
    print(" -d int, --dim int   Output image dimensions (default=32)")
    print(" -c , --cylinder     Cylinder volume (default)")
    print(" -t , --tetra        Tetrahedral volume")
    print(" -p type , --pixel type        Pixel type by name (default=UInt8)")
    print()

if __name__ == "__main__":

    dim = 32
    vtype = "cylinder"
    ptype = sitk.sitkUInt8

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:ctp:",
            [ "help", "dim", "cylinder", "tetra", "pixel=" ] )
    except getopt.GetoptError as err:
        print (str(err))
        usage()
        sys.exit(2)


    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-d", "--dim"):
            dim = int(a)
        elif o in ("-c", "--cylinder"):
            vtype = "cylinder"
        elif o in ("-t", "--tetra"):
            vtype = "tetra"
        elif o in ("-p", "--pixel"):
            if a.lower() == "uint16":
                ptype = sitk.sitkUInt16
            elif a.lower() == "int16":
                ptype = sitk.sitkInt16
            elif a.lower() == "int32":
                ptype = sitk.sitkInt32
            elif a.lower() == "float32":
                ptype = sitk.sitkFloat32
            elif a.lower() == "float64":
                ptype = sitk.sitkFloat64
        else:
            assert False, "unhandled options"

    if vtype == "tetra":
        print("Making tetra")
        vol = make_tetra(dim, ptype)
    else:
        print("Making cylinder")
        vol = make_cylinder(dim, ptype)

    print("Writing", args[0])
    sitk.WriteImage(vol, args[0])
