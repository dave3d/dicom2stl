#! /usr/bin/env python

import sys
import SimpleITK as sitk
import getopt

def make_tetra(dim=128, pixel_type=sitk.sitkUInt8):
    dim4 = dim>>2
    dim2 = dim>>1
    h = .86602540378443864676*dim2+dim4
    size =[ dim,dim,dim ]
    p1 = [dim4,dim4,dim4]
    p2 = [dim2+dim4,dim4,dim4]
    p3 = [dim2, h,dim4]
    p4 = [dim2,dim2,h]
    points = [p1,p2,p3,p4]

    sigma=[dim/6,dim/6,dim/6]
    v1 = sitk.GaussianSource(pixel_type, size, sigma=sigma, mean=p1, scale=200)
    v2 = sitk.GaussianSource(pixel_type, size, sigma=sigma, mean=p2, scale=200)
    v3 = sitk.GaussianSource(pixel_type, size, sigma=sigma, mean=p3, scale=200)
    v4 = sitk.GaussianSource(pixel_type, size, sigma=sigma, mean=p4, scale=200)

    vsum = v1+v2+v3+v4

    return vsum

def make_cylinder(dim=64, pixel_type=sitk.sitkUInt8):
    mean=[dim/2,dim/2]
    sigma=[dim/4,dim/4]
    img = sitk.GaussianSource(pixel_type, [dim,dim], sigma=sigma, mean=mean, scale=200)

    series = []
    for i in range(dim):
        series.append(img)

    vol = sitk.JoinSeries(series)
    return vol

def vol2dicom(vol, root_name):
    """ this kinda sucks.  doesn't do keep the UID tag properly. """
    for z in range(vol.GetDepth()):
       img = vol[:,:,z]
       img.SetMetaData("0020|000e", "1.2.3.4.5.6.7.8")
       name = "%s.%d.dcm" % (root_name, z)
       print(name)
       sitk.WriteImage(img, name)


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
