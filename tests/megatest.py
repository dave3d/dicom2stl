#! /usr/bin/env python

import sys, os
import SimpleITK as sitk
import glob

import compare_stats
thisdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.dirname(thisdir)
sys.path.append(os.path.abspath(parentdir))
print(sys.path)
from utils import sitk2vtk

suffixes =  ['.png', '.nrrd', '.dcm', '.nii.gz', '.dcm']

fnames = []
if len(sys.argv) == 1:
    img_dir = os.environ['HOME']+'/SimpleITK-build/SimpleITK-build/ExternalData/Testing/Data/Input'

    fnames = glob.glob(img_dir+'/*')
    fnames.extend( glob.glob(img_dir+'/**/*'))

else:
    for x in sys.argv[1:]:
        if os.path.isfile(x):
            fnames.append(x)
        if os.path.isdir(x):
            fnames.extend(glob.glob(x+'/*'))
            fnames.extend(glob.glob(x+'/**/*'))


img_names = []
for f in fnames:
    for s in suffixes:
        if f.endswith(s):
            img_names.append(f)

print(len(img_names), "images")

bad = []
pass_count = 0
unsupport_count = 0
unsupp = []

for n in img_names:
    print("\n", n)

    img = sitk.ReadImage(n)
    vtkimg = sitk2vtk.sitk2vtk(img)
    if vtkimg == None:
        print("File", n, "didn't convert")
        continue
    try:
        ok = compare_stats.compare_stats(img, vtkimg)
    except:
        print("exception: probably wrong image type")
        print("UNSUPPORTED")
        unsupport_count = unsupport_count+1
        unsupp.append(n)
        continue

    if not ok:
        bad.append(n)
        print("FAIL")
    else:
        print("PASS")
        pass_count = pass_count+1

print("\n", bad)
print(len(bad), "bad result")

print("\n", pass_count, "passed")

print("\n", unsupport_count, "unsupported")
print(unsupp)
